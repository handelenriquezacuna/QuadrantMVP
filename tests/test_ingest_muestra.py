"""Valida el esquema y la cobertura de data/muestra_bitext.parquet."""
from pathlib import Path

import pandas as pd

RUTA = Path(__file__).resolve().parent.parent / "data" / "muestra_bitext.parquet"


def test_esquema_y_filas():
    df = pd.read_parquet(RUTA)
    assert list(df.columns) == ["row_id", "flags", "instruction", "category", "intent", "response"]
    assert len(df) == 3000
    assert df["row_id"].tolist() == list(range(3000))
    assert pd.api.types.is_integer_dtype(df["row_id"])
    for col in ["flags", "instruction", "category", "intent", "response"]:
        assert pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object


def test_cobertura_categorias_e_intents():
    df = pd.read_parquet(RUTA)
    assert df["intent"].nunique() == 27
    assert df["category"].nunique() == 11
