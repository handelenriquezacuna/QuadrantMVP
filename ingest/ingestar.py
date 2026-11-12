"""Ingesta de la muestra Bitext a faq_kb. Uso: python -m ingest.ingestar"""
import os
import sys
import time

import pandas as pd
from qdrant_client import models

from app.store.busquedas import FAQ_KB
from app.store.cliente import get_client
from app.store.colecciones import crear_colecciones
from app.store.embeddings import embed_denso, embed_disperso

LOTE = 64
ESPERADOS = 3000


def ingestar(ruta: str, esperados: int = ESPERADOS) -> bool:
    """Devuelve False si ya estaba ingerido."""
    t0 = time.time()
    crear_colecciones()
    c = get_client()
    if c.count(FAQ_KB, exact=True).count >= esperados:
        print("ya ingerido")
        return False

    df = pd.read_parquet(ruta)
    total = len(df)
    for ini in range(0, total, LOTE):
        lote = df.iloc[ini:ini + LOTE]
        textos = lote["instruction"].astype(str).tolist()
        dens = embed_denso(textos)
        disp = embed_disperso(textos)
        puntos = []
        for (_, f), d, s in zip(lote.iterrows(), dens, disp):
            puntos.append(models.PointStruct(
                id=int(f["row_id"]), vector={"dense": d, "bm25": s},
                payload={"row_id": int(f["row_id"]), "instruction": str(f["instruction"]),
                         "response": str(f["response"]), "category": str(f["category"]),
                         "intent": str(f["intent"]), "flags": str(f["flags"])}))
        c.upsert(FAQ_KB, points=puntos, wait=True)
        print(f"  {min(ini + LOTE, total)}/{total}", flush=True)
    print(f"Ingesta completa: {total} filas en {time.time() - t0:.1f} s")
    return True


def main() -> int:
    ruta = os.environ.get("MUESTRA_PATH", "/app/data/muestra_bitext.parquet")
    try:
        ingestar(ruta)
    except Exception as e:  # noqa: BLE001
        print(f"Error en la ingesta: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
