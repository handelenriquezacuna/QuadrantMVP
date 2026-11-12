"""La ingesta es idempotente: con faq_kb completa dice "ya ingerido" y no toca nada."""
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.integracion


def test_ingesta_idempotente(faq_real, capsys):
    from app.store.colecciones import FAQ_KB
    from ingest.ingestar import ingestar
    ruta = os.environ.get("MUESTRA_PATH", str(Path(__file__).resolve().parent.parent / "data" / "muestra_bitext.parquet"))
    assert ingestar(ruta) is False
    assert "ya ingerido" in capsys.readouterr().out
    assert faq_real.count(FAQ_KB, exact=True).count == 3000
