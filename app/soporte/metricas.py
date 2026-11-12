"""Métricas por nodo y cálculo de costo contra precios de referencia."""
import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class MetricaNodo:
    nodo: str
    tokens_entrada: int
    tokens_salida: int
    latencia_ms: float
    cache_hit: bool = False


def cargar_precios() -> dict:
    """Lee pricing.yaml (PRICING_PATH). Devuelve {nombre: {entrada, salida, ...}}."""
    ruta = os.environ.get("PRICING_PATH") or str(
        Path(__file__).resolve().parent.parent.parent / "pricing.yaml")
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f) or {}
    # El archivo usa "modelos"; el contrato nombra "referencias". Se aceptan ambos.
    return datos.get("referencias") or datos.get("modelos") or {}


def costo_usd(tokens_entrada: int, tokens_salida: int, referencia: str) -> float:
    """Costo en USD (precios por millón de tokens)."""
    p = cargar_precios()[referencia]
    return (tokens_entrada * p["entrada"] + tokens_salida * p["salida"]) / 1_000_000
