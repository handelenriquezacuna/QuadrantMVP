"""Pruebas de integración de app/store contra el faq_kb real (solo lectura)."""
import pytest

from app.store import busquedas as b
from app.store.cliente import probar_api_key
from app.store.colecciones import ANSWER_CACHE, FAQ_KB, info_coleccion, listar_colecciones
from app.store.embeddings import embed_denso

pytestmark = pytest.mark.integracion


def test_colecciones_e_info(faq_real):
    assert {FAQ_KB, ANSWER_CACHE} <= set(listar_colecciones())
    i = info_coleccion(FAQ_KB)
    assert i["puntos"] == 3000
    assert i["hnsw"] == {"m": 16, "ef_construct": 100}
    assert i["cuantizacion"]["tipo"] == "int8"
    assert {"dense", "bm25"} <= set(i["vectores"])
    assert {"category", "intent", "instruction"} <= set(i["indices_payload"])
    assert i["memoria_estimada_mb"]["int8"] < i["memoria_estimada_mb"]["float32"]


def test_consulta_en_espanol_devuelve_faq_en_ingles(faq_real):
    r = b.buscar_denso("¿Cómo cambio mi contraseña olvidada?", top_k=5)
    assert any("password" in x.instruction.lower() for x in r)


def test_denso_disperso_hibrido_difieren(faq_real):
    q = "order refund invoice"
    ids = [tuple(x.id for x in f(q, top_k=5)) for f in (b.buscar_denso, b.buscar_disperso, b.buscar_hibrido)]
    assert len(set(ids)) == 3, ids


def test_filtro_category(faq_real):
    cat = b.listar_valores("category")[0]
    for f in (b.buscar_denso, b.buscar_disperso, b.buscar_hibrido):
        r = f("account order refund invoice payment", top_k=5, category=cat)
        assert r and all(x.category == cat for x in r)


def test_palabra_exacta(faq_real):
    r = b.buscar_palabra_exacta("invoice")
    assert r and all("invoice" in x.instruction.lower() for x in r)
    assert all(x.score == 0.0 for x in r)


def test_recomendar_excluye_ejemplos(faq_real):
    ej = [x.id for x in b.buscar_denso("cancel my order", top_k=3)]
    pos, neg = ej[:2], ej[2:]
    for est in ("average_vector", "best_score"):
        r = b.recomendar(pos, neg, top_k=5, estrategia=est)
        assert r and not set(ej) & {x.id for x in r}


def test_listar_valores_y_obtener_punto(faq_real):
    cats = b.listar_valores("category")
    assert len(cats) > 1
    intents = b.listar_valores("intent", category=cats[0])
    assert intents and set(intents) <= set(b.listar_valores("intent"))
    p = b.buscar_denso("reset password", top_k=1)[0]
    assert b.obtener_punto(p.id).instruction == p.instruction
    assert b.obtener_punto(10**9) is None


def test_probar_api_key(qdrant):
    r = probar_api_key()
    assert r["sin_clave"] in (401, 403)
    assert r["clave_incorrecta"] in (401, 403)
    assert r["con_clave"] == 200


def test_cache_respeta_umbral(faq_real):
    from qdrant_client import models
    pregunta = "prueba-test: How do I reset my password?"
    v = embed_denso([pregunta])[0]
    antes = b.cache_contar()
    b.cache_guardar(pregunta, v, "Use el enlace.", "ACCOUNT", "recover_password", "prueba")
    try:
        assert b.cache_contar() == antes + 1
        hit = b.cache_buscar(v, 0.92)
        assert hit and hit.response == "Use el enlace."
        otro = embed_denso(["Where is the nearest pizza restaurant?"])[0]
        assert b.cache_buscar(otro, 0.92) is None
    finally:
        faq_real.delete(ANSWER_CACHE, points_selector=models.Filter(must=[models.FieldCondition(
            key="modelo", match=models.MatchValue(value="prueba"))]), wait=True)
