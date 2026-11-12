"""Embeddings locales con fastembed (denso y disperso BM25)."""
import os
from functools import lru_cache

from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client import models


def _cache() -> str | None:
    return os.environ.get("FASTEMBED_CACHE_PATH") or None


@lru_cache(maxsize=1)
def _modelo_denso() -> TextEmbedding:
    nombre = os.environ.get(
        "DENSE_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return TextEmbedding(model_name=nombre, cache_dir=_cache())


@lru_cache(maxsize=1)
def _modelo_disperso() -> SparseTextEmbedding:
    nombre = os.environ.get("SPARSE_MODEL", "Qdrant/bm25")
    return SparseTextEmbedding(model_name=nombre, cache_dir=_cache())


def embed_denso(textos: list[str]) -> list[list[float]]:
    """Un vector de 384 floats por texto."""
    return [v.tolist() for v in _modelo_denso().embed(textos)]


def embed_disperso(textos: list[str], consulta: bool = False) -> list[models.SparseVector]:
    """Vectores BM25. Con consulta=True usa el modo de consulta (sin saturación de frecuencia)."""
    modelo = _modelo_disperso()
    gen = modelo.query_embed(textos) if consulta else modelo.embed(textos)
    return [models.SparseVector(indices=v.indices.tolist(), values=v.values.tolist())
            for v in gen]
