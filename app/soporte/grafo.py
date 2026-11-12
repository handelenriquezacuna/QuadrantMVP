"""Grafo de soporte: triage -> retriever -> responder -> qa (LangGraph)."""
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, StateGraph

from app.store import busquedas, embeddings

from .metricas import MetricaNodo
from .ollama import chat

SISTEMA_RESPONDER = ("Eres un agente de soporte al cliente. Responde siempre en español, "
                     "de forma breve y amable, usando SOLO el contexto dado. "
                     "Si el contexto no alcanza, dilo.")
SISTEMA_QA = ("Eres un revisor de calidad. Responde únicamente SI o NO: "
              "¿la respuesta contesta la pregunta y es coherente con el contexto?")
SISTEMA_CLASIFICADOR = ("Clasifica la pregunta del cliente en una de estas categorías: {cats}. "
                        "Responde solo con el nombre de la categoría.")


@dataclass
class ResultadoConsulta:
    pregunta: str
    respuesta: str
    category: str
    intent: str
    cache_hit: bool
    aprobado_qa: bool
    metricas: list[MetricaNodo] = field(default_factory=list)

    def tokens_totales(self) -> int:
        return sum(m.tokens_entrada + m.tokens_salida for m in self.metricas)

    def latencia_total_ms(self) -> float:
        return sum(m.latencia_ms for m in self.metricas)


class Estado(TypedDict, total=False):
    pregunta: str
    umbral: float
    vector: list[float]
    category: str
    intent: str
    contexto: list
    respuesta: str
    cache_hit: bool
    aprobado_qa: bool
    metricas: list[MetricaNodo]


def _umbral_defecto() -> float:
    return float(os.environ.get("CACHE_THRESHOLD", "0.92"))


def _contexto_texto(resultados) -> str:
    return "\n\n".join(f"P: {r.instruction}\nR: {r.response}" for r in resultados)


def _llamar(llm, nodo: str, sistema: str, usuario: str, estado: Estado):
    """Llama al LLM y anota la métrica del nodo con los tokens reales."""
    r = llm(sistema, usuario)
    estado["metricas"].append(MetricaNodo(nodo, r.tokens_entrada, r.tokens_salida, r.latencia_ms))
    return r


def _construir(llm):
    def triage(e: Estado) -> Estado:
        t0 = time.perf_counter()
        vector = embeddings.embed_denso([e["pregunta"]])[0]
        e["vector"] = vector
        golpe = busquedas.cache_buscar(vector, e["umbral"])
        if golpe is not None:
            e.update(cache_hit=True, respuesta=golpe.response,
                     category=golpe.category, intent=golpe.intent, aprobado_qa=True)
        else:
            vecinos = busquedas.buscar_denso(vector, top_k=5)
            # Voto mayoritario entre los 5 vecinos
            e["category"] = Counter(v.category for v in vecinos).most_common(1)[0][0] if vecinos else ""
            e["intent"] = Counter(v.intent for v in vecinos).most_common(1)[0][0] if vecinos else ""
        e["metricas"].append(MetricaNodo("triage", 0, 0, (time.perf_counter() - t0) * 1000,
                                         cache_hit=golpe is not None))
        return e

    def retriever(e: Estado) -> Estado:
        t0 = time.perf_counter()
        e["contexto"] = busquedas.buscar_denso(e["vector"], top_k=3, category=e["category"] or None)
        e["metricas"].append(MetricaNodo("retriever", 0, 0, (time.perf_counter() - t0) * 1000))
        return e

    def responder(e: Estado) -> Estado:
        usuario = f"Contexto:\n{_contexto_texto(e['contexto'])}\n\nPregunta: {e['pregunta']}"
        e["respuesta"] = _llamar(llm, "responder", SISTEMA_RESPONDER, usuario, e).texto
        return e

    def qa(e: Estado) -> Estado:
        usuario = (f"Pregunta: {e['pregunta']}\nContexto:\n{_contexto_texto(e['contexto'])}\n"
                   f"Respuesta: {e['respuesta']}")
        veredicto = _llamar(llm, "qa", SISTEMA_QA, usuario, e).texto.strip().upper()
        e["aprobado_qa"] = veredicto.startswith("SI") or veredicto.startswith("SÍ")
        if e["aprobado_qa"]:
            busquedas.cache_guardar(e["pregunta"], e["vector"], e["respuesta"], e["category"],
                                    e["intent"], os.environ.get("OLLAMA_MODEL", "llama3.2:3b"))
        return e

    g = StateGraph(Estado)
    g.add_node("triage", triage)
    g.add_node("retriever", retriever)
    g.add_node("responder", responder)
    g.add_node("qa", qa)
    g.set_entry_point("triage")
    g.add_conditional_edges("triage", lambda e: END if e.get("cache_hit") else "retriever")
    g.add_edge("retriever", "responder")
    g.add_edge("responder", "qa")
    g.add_edge("qa", END)
    return g.compile()


def responder_con_qdrant(pregunta: str, umbral: float | None = None, llm=chat) -> ResultadoConsulta:
    """Ejecuta el grafo completo. Un acierto de caché termina tras el triage con 0 tokens."""
    final = _construir(llm).invoke({
        "pregunta": pregunta,
        "umbral": _umbral_defecto() if umbral is None else umbral,
        "cache_hit": False, "aprobado_qa": False, "metricas": [],
    })
    return ResultadoConsulta(pregunta, final.get("respuesta", ""), final.get("category", ""),
                             final.get("intent", ""), final["cache_hit"], final["aprobado_qa"],
                             final["metricas"])


def _faqs_de_categoria(category: str, n: int = 30) -> list[tuple[str, str]]:
    import pandas as pd
    ruta = os.environ.get("MUESTRA_PATH") or str(
        Path(__file__).resolve().parent.parent.parent / "data" / "muestra_bitext.parquet")
    df = pd.read_parquet(ruta)
    return list(df[df["category"] == category].head(n)[["instruction", "response"]]
                .itertuples(index=False, name=None))


def responder_sin_qdrant(pregunta: str, llm=chat, categorias: list[str] | None = None) -> ResultadoConsulta:
    """Sin base vectorial: el LLM clasifica y el prompt lleva 30 FAQs de esa categoría."""
    import pandas as pd
    metricas: list[MetricaNodo] = []
    if categorias is None:
        ruta = os.environ.get("MUESTRA_PATH") or str(
            Path(__file__).resolve().parent.parent.parent / "data" / "muestra_bitext.parquet")
        categorias = sorted(pd.read_parquet(ruta, columns=["category"])["category"].unique())
    est: Estado = {"metricas": metricas}
    r = _llamar(llm, "clasificador", SISTEMA_CLASIFICADOR.format(cats=", ".join(categorias)),
                pregunta, est)
    texto = r.texto.strip().upper()
    category = next((c for c in categorias if c in texto), "")
    faqs = _faqs_de_categoria(category) if category else []
    contexto = "\n\n".join(f"P: {p}\nR: {rr}" for p, rr in faqs)
    r2 = _llamar(llm, "responder", SISTEMA_RESPONDER,
                 f"Contexto:\n{contexto}\n\nPregunta: {pregunta}", est)
    return ResultadoConsulta(pregunta, r2.texto, category, "", False, True, metricas)
