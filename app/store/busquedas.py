"""Búsquedas sobre faq_kb y operaciones sobre answer_cache."""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from qdrant_client import models

from .cliente import get_client
from .colecciones import ANSWER_CACHE, FAQ_KB
from .embeddings import embed_denso, embed_disperso


@dataclass
class Resultado:
    id: int | str
    score: float
    instruction: str
    response: str
    category: str
    intent: str


def _a_resultado(p, score: float | None = None) -> Resultado:
    d = p.payload or {}
    return Resultado(
        id=p.id,
        score=float(score if score is not None else getattr(p, "score", 0.0) or 0.0),
        instruction=d.get("instruction", ""), response=d.get("response", ""),
        category=d.get("category", ""), intent=d.get("intent", ""),
    )


def _filtro(category: str | None, intent: str | None) -> models.Filter | None:
    cond = []
    if category:
        cond.append(models.FieldCondition(key="category", match=models.MatchValue(value=category)))
    if intent:
        cond.append(models.FieldCondition(key="intent", match=models.MatchValue(value=intent)))
    return models.Filter(must=cond) if cond else None


def buscar_denso(consulta: str | list[float], top_k: int = 5,
                 category: str | None = None, intent: str | None = None) -> list[Resultado]:
    """Búsqueda semántica. Acepta texto o un vector ya calculado."""
    vec = embed_denso([consulta])[0] if isinstance(consulta, str) else consulta
    r = get_client().query_points(FAQ_KB, query=vec, using="dense", limit=top_k,
                                  query_filter=_filtro(category, intent), with_payload=True)
    return [_a_resultado(p) for p in r.points]


def buscar_disperso(consulta: str, top_k: int = 5,
                    category: str | None = None, intent: str | None = None) -> list[Resultado]:
    """Búsqueda léxica BM25."""
    vec = embed_disperso([consulta], consulta=True)[0]
    r = get_client().query_points(FAQ_KB, query=vec, using="bm25", limit=top_k,
                                  query_filter=_filtro(category, intent), with_payload=True)
    return [_a_resultado(p) for p in r.points]


def buscar_hibrido(consulta: str, top_k: int = 5,
                   category: str | None = None, intent: str | None = None) -> list[Resultado]:
    """Denso + BM25 fusionados con RRF."""
    f = _filtro(category, intent)
    dv = embed_denso([consulta])[0]
    sv = embed_disperso([consulta], consulta=True)[0]
    r = get_client().query_points(
        FAQ_KB,
        prefetch=[
            models.Prefetch(query=dv, using="dense", limit=20, filter=f),
            models.Prefetch(query=sv, using="bm25", limit=20, filter=f),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k, with_payload=True)
    return [_a_resultado(p) for p in r.points]


def buscar_palabra_exacta(consulta: str, top_k: int = 5) -> list[Resultado]:
    """Filtro de texto completo sobre 'instruction' (sin ranking: score 0.0)."""
    filtro = models.Filter(must=[models.FieldCondition(
        key="instruction", match=models.MatchText(text=consulta))])
    puntos, _ = get_client().scroll(FAQ_KB, scroll_filter=filtro, limit=top_k, with_payload=True)
    return [_a_resultado(p, 0.0) for p in puntos]


def recomendar(positivos: list[int], negativos: list[int], top_k: int = 5,
               estrategia: str = "average_vector") -> list[Resultado]:
    """Recomienda por ejemplos; Qdrant excluye los ejemplos del resultado."""
    est = models.RecommendStrategy(estrategia)
    r = get_client().query_points(
        FAQ_KB,
        query=models.RecommendQuery(recommend=models.RecommendInput(
            positive=positivos, negative=negativos or None, strategy=est)),
        using="dense", limit=top_k, with_payload=True)
    return [_a_resultado(p) for p in r.points]


def listar_valores(campo: str, category: str | None = None) -> list[str]:
    """Valores distintos de 'category' o 'intent' (facet), opcionalmente dentro de una categoría."""
    if campo not in ("category", "intent"):
        raise ValueError("campo debe ser 'category' o 'intent'")
    filtro = _filtro(category, None)
    r = get_client().facet(FAQ_KB, key=campo, facet_filter=filtro, limit=1000)
    return sorted(str(h.value) for h in r.hits)


def obtener_punto(id: int) -> Resultado | None:
    pts = get_client().retrieve(FAQ_KB, ids=[id], with_payload=True)
    return _a_resultado(pts[0], 0.0) if pts else None


def cache_buscar(vector: list[float], umbral: float) -> Resultado | None:
    """Top-1 del caché; None si no alcanza el umbral."""
    r = get_client().query_points(ANSWER_CACHE, query=vector, using="dense",
                                  limit=1, with_payload=True)
    if not r.points or r.points[0].score < umbral:
        return None
    p = r.points[0]
    d = p.payload or {}
    return Resultado(id=p.id, score=float(p.score), instruction=d.get("pregunta", ""),
                     response=d.get("respuesta", ""), category=d.get("category", ""),
                     intent=d.get("intent", ""))


def cache_guardar(pregunta: str, vector: list[float], respuesta: str,
                  category: str, intent: str, modelo: str) -> None:
    """Guarda (o sobrescribe) una respuesta; el id sale de la pregunta normalizada."""
    norm = " ".join(pregunta.lower().split())
    pid = str(uuid.uuid5(uuid.NAMESPACE_URL, norm))
    get_client().upsert(ANSWER_CACHE, points=[models.PointStruct(
        id=pid, vector={"dense": vector},
        payload={"pregunta": pregunta, "respuesta": respuesta, "category": category,
                 "intent": intent, "modelo": modelo,
                 "creado_en": datetime.now(timezone.utc).isoformat()})], wait=True)
