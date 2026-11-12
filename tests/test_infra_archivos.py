"""Pruebas de infraestructura: archivos de configuración coherentes."""
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
if not (RAIZ / "docker-compose.yml").exists():
    RAIZ = Path("/app")


def test_compose_sin_latest():
    texto = (RAIZ / "docker-compose.yml").read_text()
    assert "latest" not in texto


def test_pricing_tiene_tres_referencias():
    datos = yaml.safe_load((RAIZ / "pricing.yaml").read_text())
    assert len(datos["modelos"]) == 3


def test_compose_ollama_en_profile_llm():
    datos = yaml.safe_load((RAIZ / "docker-compose.yml").read_text())
    servicios = datos["services"]
    for nombre in ("ollama", "ollama-pull"):
        assert servicios[nombre]["profiles"] == ["llm"]
    dep = servicios["app"]["depends_on"]["ollama-pull"]
    assert dep["required"] is False
