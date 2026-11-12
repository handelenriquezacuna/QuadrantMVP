"""Genera data/muestra_bitext.parquet: 3,000 filas estratificadas por intent.

Uso: python -I ingest/preparar_muestra.py RUTA_CSV [RUTA_PARQUET]
"""
import sys
from pathlib import Path

import pandas as pd

TOTAL = 3000
SEMILLA = 42
COLUMNAS = ["flags", "instruction", "category", "intent", "response"]
SALIDA_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "muestra_bitext.parquet"


def cuotas_por_intent(conteos: pd.Series, total: int) -> pd.Series:
    """Reparte `total` filas proporcionalmente por intent (mayores restos)."""
    exacto = conteos / conteos.sum() * total
    cuotas = exacto.astype(int).clip(lower=1)  # al menos 1 por intent
    faltan = total - int(cuotas.sum())
    restos = (exacto - exacto.astype(int)).sort_values(ascending=False, kind="stable")
    for intent in restos.index[:faltan]:
        cuotas[intent] += 1
    return cuotas


def preparar(ruta_csv: str, ruta_salida: Path = SALIDA_DEFECTO) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv, usecols=COLUMNAS, dtype=str, keep_default_na=False)
    df = df.sort_values(COLUMNAS, kind="stable").reset_index(drop=True)  # orden determinista
    cuotas = cuotas_por_intent(df["intent"].value_counts().sort_index(), TOTAL)
    partes = [
        grupo.sample(n=int(cuotas[intent]), random_state=SEMILLA)
        for intent, grupo in df.groupby("intent", sort=True)
    ]
    muestra = pd.concat(partes).sample(frac=1, random_state=SEMILLA).reset_index(drop=True)
    muestra.insert(0, "row_id", range(len(muestra)))
    muestra["row_id"] = muestra["row_id"].astype("int64")
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    muestra.to_parquet(ruta_salida, index=False)
    return muestra


if __name__ == "__main__":
    destino = Path(sys.argv[2]) if len(sys.argv) > 2 else SALIDA_DEFECTO
    m = preparar(sys.argv[1], destino)
    print(f"{len(m)} filas, {m['intent'].nunique()} intents -> {destino}")
