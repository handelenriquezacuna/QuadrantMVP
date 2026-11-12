"""Tests de la pestaña 5 con AppTest. No requieren red, Qdrant ni Ollama."""
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from app.soporte import grafo, ollama
from app.store import busquedas
from app.soporte.grafo import ResultadoConsulta
from app.soporte.metricas import MetricaNodo


def _app():
    from app.ui import tab5_soporte
    tab5_soporte.render()


def _csv(ruta):
    filas = []
    for i, (grupo, hit) in enumerate([("original", False), ("parafrasis", True)] * 2):
        for modo, ent, sal, lat in (("con_qdrant", 0 if hit else 200, 0 if hit else 50, 800),
                                    ("sin_qdrant", 900, 60, 2000)):
            filas.append(dict(pregunta_id=i, pregunta="¿Cómo cancelo?", grupo=grupo, modo=modo,
                              cache_hit=hit and modo == "con_qdrant", tokens_entrada=ent,
                              tokens_salida=sal, latencia_ms=lat, category_predicha="ORDER",
                              category_real="ORDER", modelo="m"))
    pd.DataFrame(filas).to_csv(ruta, index=False)


def test_sin_ollama_muestra_benchmark(tmp_path, monkeypatch):
    ruta = tmp_path / "b.csv"
    _csv(ruta)
    monkeypatch.setenv("BENCHMARK_PATH", str(ruta))
    monkeypatch.setattr(ollama, "disponible", lambda: False)
    at = AppTest.from_function(_app, default_timeout=60).run()
    assert not at.exception
    assert any("Ollama no está disponible" in w.value for w in at.warning)
    assert len(at.metric) == 4
    valores = [m.value for m in at.metric]
    assert "2 / 2" in valores          # caché en paráfrasis
    assert "100 % / 100 %" in valores  # categoría correcta con / sin


def test_csv_faltante_mensaje_claro(tmp_path, monkeypatch):
    monkeypatch.setenv("BENCHMARK_PATH", str(tmp_path / "no_existe.csv"))
    monkeypatch.setattr(ollama, "disponible", lambda: False)
    at = AppTest.from_function(_app, default_timeout=60).run()
    assert not at.exception
    assert any("No se encontró un benchmark" in w.value for w in at.warning)


def test_modo_en_vivo(tmp_path, monkeypatch):
    ruta = tmp_path / "b.csv"
    _csv(ruta)
    monkeypatch.setenv("BENCHMARK_PATH", str(ruta))
    monkeypatch.setattr(ollama, "disponible", lambda: True)

    def falso(pregunta, *a, **k):
        m = [MetricaNodo("responder", 100, 20, 50.0)]
        return ResultadoConsulta(pregunta, "Respuesta", "ORDER", "cancel_order", False, True, m)

    monkeypatch.setattr(grafo, "responder_con_qdrant", falso)
    monkeypatch.setattr(grafo, "responder_sin_qdrant", falso)
    monkeypatch.setattr(busquedas, "cache_contar", lambda: 3)
    at = AppTest.from_function(_app, default_timeout=60).run()
    at.text_input(key="t5_pregunta").set_value("¿Cómo cancelo?")
    at = at.button(key="t5_consultar").click().run()
    assert not at.exception
    assert len(at.dataframe) == 2
    assert len(at.metric) == 9


def test_vaciar_cache(tmp_path, monkeypatch):
    ruta = tmp_path / "b.csv"
    _csv(ruta)
    monkeypatch.setenv("BENCHMARK_PATH", str(ruta))
    monkeypatch.setattr(ollama, "disponible", lambda: True)
    estado = {"n": 5}
    monkeypatch.setattr(busquedas, "cache_contar", lambda: estado["n"])

    def vaciar():
        n, estado["n"] = estado["n"], 0
        return n

    monkeypatch.setattr(busquedas, "cache_vaciar", vaciar)
    at = AppTest.from_function(_app, default_timeout=60).run()
    assert any("caché semántica: 5" in c.value for c in at.caption)
    at = at.button(key="t5_vaciar").click().run()
    assert not at.exception
    assert any("caché semántica: 0" in c.value for c in at.caption)
