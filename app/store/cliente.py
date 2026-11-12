"""Cliente de Qdrant (singleton) y prueba de la API key."""
import os

import httpx
from qdrant_client import QdrantClient

_cliente: QdrantClient | None = None


def _url() -> str:
    return os.environ.get("QDRANT_URL", "http://qdrant:6333")


def _clave() -> str:
    return os.environ.get("QDRANT_API_KEY", "qdrant-lab-clave-local-cambiar")


def get_client() -> QdrantClient:
    """Devuelve el mismo cliente en todas las llamadas."""
    global _cliente
    if _cliente is None:
        _cliente = QdrantClient(url=_url(), api_key=_clave(), timeout=60,
                                check_compatibility=False)
    return _cliente


def probar_api_key() -> dict:
    """Consulta GET /collections sin clave, con clave incorrecta y con la correcta."""
    url = f"{_url()}/collections"
    casos = {
        "sin_clave": {},
        "clave_incorrecta": {"api-key": "clave-incorrecta"},
        "con_clave": {"api-key": _clave()},
    }
    return {n: httpx.get(url, headers=h, timeout=10).status_code
            for n, h in casos.items()}
