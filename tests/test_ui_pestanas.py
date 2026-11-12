"""Tests de la UI con AppTest. Requieren Qdrant con faq_kb poblada."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

pytestmark = pytest.mark.integracion
MAIN = str(Path(__file__).resolve().parent.parent / "app" / "main.py")


def test_pestanas_renderizan_sin_excepcion(faq_real):
    at = AppTest.from_file(MAIN, default_timeout=120).run()
    assert not at.exception
    assert len(at.tabs) == 6


def test_pestana6_muestra_rechazo_sin_api_key(faq_real):
    at = AppTest.from_file(MAIN, default_timeout=120).run()
    boton = next(b for b in at.button if b.key == "t6_probar")
    at = boton.click().run()
    assert not at.exception
    assert any("rechaza sin clave" in s.value for s in at.success)


def test_ui_no_usa_qdrant_client_directo():
    for f in (Path(MAIN).parent / "ui").glob("*.py"):
        assert "qdrant_client" not in f.read_text(), f.name
