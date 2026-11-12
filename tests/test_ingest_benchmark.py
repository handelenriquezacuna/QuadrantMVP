"""Pruebas del benchmark sin red ni Ollama."""
from types import SimpleNamespace

from app.soporte.metricas import MetricaNodo
from ingest import benchmark


def test_yaml_tiene_50_originales_y_50_parafrasis():
    ps = benchmark.cargar_preguntas()
    assert len(ps) == 100
    assert sum(p["grupo"] == "original" for p in ps) == 50
    assert len({p["category_real"] for p in ps}) == 11
    ids = {p["pregunta_id"] for p in ps}
    assert all(p["pregunta_id"].endswith("p") == (p["grupo"] == "parafrasis") for p in ps)
    assert len(ids) == 100


def test_plan_orden_y_total():
    pl = benchmark.plan(benchmark.cargar_preguntas())
    assert len(pl) == 200
    assert [m for _, m in pl[:100]] == ["con_qdrant"] * 100
    assert [g["grupo"] for g, _ in pl[:50]] == ["original"] * 50
    assert all(m == "sin_qdrant" for _, m in pl[100:])


def test_fila_suma_tokens_reales():
    r = SimpleNamespace(cache_hit=False, category="ORDER", metricas=[
        MetricaNodo("responder", 10, 5, 100.0), MetricaNodo("qa", 3, 1, 50.0)],
        latencia_total_ms=lambda: 150.0)
    p = {"pregunta_id": "Q01", "pregunta": "x", "grupo": "original", "category_real": "ORDER"}
    f = benchmark.fila_de(p, "con_qdrant", r, "m")
    assert (f["tokens_entrada"], f["tokens_salida"], f["latencia_ms"]) == (13, 6, 150.0)
    assert set(f) == set(benchmark.COLUMNAS)
