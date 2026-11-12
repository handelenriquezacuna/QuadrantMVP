"""Fixtures compartidas. Los tests nunca borran ni recrean colecciones de la app."""
import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _qdrant_responde() -> bool:
    import httpx
    url = os.environ.get("QDRANT_URL")
    if not url:
        return False
    try:
        httpx.get(f"{url}/collections", timeout=3,
                  headers={"api-key": os.environ.get("QDRANT_API_KEY", "")})
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture(scope="session")
def qdrant():
    """Salta el test si no hay Qdrant en QDRANT_URL."""
    if not _qdrant_responde():
        pytest.skip("Qdrant no responde en QDRANT_URL; levanta el servicio para correr integración")
    from app.store.cliente import get_client
    return get_client()


@pytest.fixture(scope="session")
def faq_real(qdrant):
    """Garantiza que faq_kb tenga los datos: si falta, corre la ingesta idempotente."""
    from app.store.colecciones import FAQ_KB, crear_colecciones
    crear_colecciones()
    if qdrant.count(FAQ_KB, exact=True).count < 3000:
        from ingest.ingestar import ingestar
        ruta = os.environ.get("MUESTRA_PATH", str(RAIZ / "data" / "muestra_bitext.parquet"))
        if not Path(ruta).exists():
            ruta = str(RAIZ / "data" / "muestra_bitext.parquet")
        ingestar(ruta)
    return qdrant
