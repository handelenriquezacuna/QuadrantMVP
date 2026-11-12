"""Pruebas del grafo de soporte con LLM falso y almacén simulado (sin red)."""
import time

import pytest

from app.soporte import grafo, metricas, ollama
from app.soporte.ollama import RespuestaLLM
from app.store.busquedas import Resultado


def _res(i, cat="ORDER", intent="cancel_order"):
    return Resultado(id=i, score=0.9, instruction=f"p{i}", response=f"r{i}", category=cat, intent=intent)


class LLMFalso:
    def __init__(self, qa="SI"):
        self.llamadas = []
        self.qa = qa

    def __call__(self, sistema, usuario, modelo=None):
        self.llamadas.append(sistema)
        texto = self.qa if "revisor" in sistema else "Respuesta en español"
        return RespuestaLLM(texto, 11, 7, 5.0)


@pytest.fixture
def almacen(monkeypatch):
    guardados = []
    monkeypatch.setattr(grafo.embeddings, "embed_denso", lambda t: [[0.1, 0.2] for _ in t])
    monkeypatch.setattr(grafo.busquedas, "buscar_denso",
                        lambda v, top_k=5, category=None, intent=None:
                        [_res(1), _res(2), _res(3, "REFUND", "x")][:top_k])
    monkeypatch.setattr(grafo.busquedas, "cache_guardar", lambda *a: guardados.append(a))
    monkeypatch.setattr(grafo.busquedas, "cache_buscar", lambda v, u: None)
    return guardados


def test_acierto_de_cache_cero_tokens(almacen, monkeypatch):
    monkeypatch.setattr(grafo.busquedas, "cache_buscar", lambda v, u: _res(9, "REFUND", "get_refund"))
    llm = LLMFalso()
    r = grafo.responder_con_qdrant("hola", llm=llm)
    assert r.cache_hit and r.tokens_totales() == 0 and r.respuesta == "r9"
    assert [m.nodo for m in r.metricas] == ["triage"] and llm.llamadas == []


def test_fallo_de_cache_cuatro_metricas_y_guarda(almacen):
    r = grafo.responder_con_qdrant("hola", llm=LLMFalso())
    assert [m.nodo for m in r.metricas] == ["triage", "retriever", "responder", "qa"]
    assert r.tokens_totales() == 36 and r.category == "ORDER" and r.aprobado_qa
    assert len(almacen) == 1


def test_qa_no_no_guarda(almacen):
    r = grafo.responder_con_qdrant("hola", llm=LLMFalso(qa="NO"))
    assert not r.aprobado_qa and almacen == []


def test_sin_qdrant_30_faqs():
    vistos = {}

    def llm(sistema, usuario, modelo=None):
        vistos[sistema[:10]] = usuario
        return RespuestaLLM("ORDER" if "Clasifica" in sistema else "ok", 3, 2, 1.0)

    r = grafo.responder_sin_qdrant("¿dónde está mi pedido?", llm=llm)
    assert [m.nodo for m in r.metricas] == ["clasificador", "responder"]
    assert r.category == "ORDER"
    prompt = vistos[grafo.SISTEMA_RESPONDER[:10]]
    assert prompt.count("P: ") == 30


def test_disponible_false_rapido_sin_ollama(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")
    t0 = time.perf_counter()
    assert ollama.disponible() is False
    assert time.perf_counter() - t0 < 3


def test_chat_usa_conteos_reales(monkeypatch):
    class R:
        def raise_for_status(self): pass
        def json(self): return {"message": {"content": " hola "}, "prompt_eval_count": 42, "eval_count": 8}
    monkeypatch.setattr(ollama.httpx, "post", lambda *a, **k: R())
    r = ollama.chat("s", "u")
    assert (r.texto, r.tokens_entrada, r.tokens_salida) == ("hola", 42, 8)


def test_costo_usd():
    precios = metricas.cargar_precios()
    nombre = next(iter(precios))
    p = precios[nombre]
    assert metricas.costo_usd(1_000_000, 1_000_000, nombre) == pytest.approx(p["entrada"] + p["salida"])


@pytest.mark.integracion
def test_integracion_cache_real_limpia(qdrant, faq_real):
    """Flujo real con Qdrant: guarda en answer_cache y elimina el punto al terminar."""
    import uuid
    from qdrant_client import models
    from app.store.colecciones import ANSWER_CACHE
    pregunta = "test_soporte pregunta única sobre mi pedido perdido"
    pid = str(uuid.uuid5(uuid.NAMESPACE_URL, " ".join(pregunta.lower().split())))
    try:
        r = grafo.responder_con_qdrant(pregunta, llm=LLMFalso())
        assert not r.cache_hit and r.aprobado_qa
        r2 = grafo.responder_con_qdrant(pregunta, llm=LLMFalso())
        assert r2.cache_hit and r2.tokens_totales() == 0
    finally:
        qdrant.delete(ANSWER_CACHE, points_selector=models.PointIdsList(points=[pid]), wait=True)
