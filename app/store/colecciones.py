"""Creación e inspección de las colecciones faq_kb y answer_cache."""
from qdrant_client import models

from .cliente import get_client

FAQ_KB = "faq_kb"
ANSWER_CACHE = "answer_cache"
DIM = 384


def crear_colecciones(recrear: bool = False) -> None:
    """Crea ambas colecciones si no existen (o las recrea con recrear=True)."""
    c = get_client()
    existentes = set(listar_colecciones())
    if recrear:
        for n in (FAQ_KB, ANSWER_CACHE):
            if n in existentes:
                c.delete_collection(n)
        existentes = set()

    if FAQ_KB not in existentes:
        c.create_collection(
            collection_name=FAQ_KB,
            vectors_config={"dense": models.VectorParams(size=DIM, distance=models.Distance.COSINE)},
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8, quantile=0.99, always_ram=True)),
        )
        c.create_payload_index(FAQ_KB, "category", models.PayloadSchemaType.KEYWORD)
        c.create_payload_index(FAQ_KB, "intent", models.PayloadSchemaType.KEYWORD)
        c.create_payload_index(
            FAQ_KB, "instruction",
            models.TextIndexParams(type=models.TextIndexType.TEXT,
                                   tokenizer=models.TokenizerType.WORD, lowercase=True))

    if ANSWER_CACHE not in existentes:
        c.create_collection(
            collection_name=ANSWER_CACHE,
            vectors_config={"dense": models.VectorParams(size=DIM, distance=models.Distance.COSINE)},
        )
        c.create_payload_index(ANSWER_CACHE, "category", models.PayloadSchemaType.KEYWORD)


def listar_colecciones() -> list[str]:
    return [x.name for x in get_client().get_collections().collections]


def _vec_info(p) -> dict:
    return {"tamano": p.size, "distancia": str(getattr(p.distance, "value", p.distance))}


def info_coleccion(nombre: str) -> dict:
    """Resumen de la colección para mostrar en la UI."""
    i = get_client().get_collection(nombre)
    cfg = i.config
    puntos = i.points_count or 0

    vp = cfg.params.vectors
    vectores = {k: _vec_info(v) for k, v in vp.items()} if isinstance(vp, dict) else {"": _vec_info(vp)}
    for k, v in (cfg.params.sparse_vectors or {}).items():
        mod = v.modifier
        vectores[k] = {"tipo": "disperso", "modificador": str(getattr(mod, "value", mod))}

    hnsw = cfg.hnsw_config
    cuant = None
    q = cfg.quantization_config
    if q is not None and getattr(q, "scalar", None) is not None:
        s = q.scalar
        cuant = {"tipo": str(getattr(s.type, "value", s.type)), "quantile": s.quantile,
                 "always_ram": s.always_ram}

    indices = {k: str(getattr(v.data_type, "value", v.data_type))
               for k, v in (i.payload_schema or {}).items()}

    # Solo los vectores densos cuentan para la estimación
    dims = sum(v["tamano"] for v in vectores.values() if "tamano" in v)
    mb_f32 = puntos * dims * 4 / 1024 / 1024
    return {
        "puntos": puntos,
        "segmentos": i.segments_count,
        "estado": str(getattr(i.status, "value", i.status)),
        "hnsw": {"m": hnsw.m, "ef_construct": hnsw.ef_construct},
        "cuantizacion": cuant,
        "vectores": vectores,
        "indices_payload": indices,
        "memoria_estimada_mb": {"float32": mb_f32, "int8": mb_f32 / 4},
    }
