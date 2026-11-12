"""Benchmark grabado: 100 preguntas (50 originales + 50 paráfrasis) en dos modos.

Uso: python -m ingest.benchmark
Escribe cada fila al CSV apenas termina y se puede retomar: salta las filas ya escritas.
Los tokens salen de Ollama (nunca se estiman).
"""
import csv
import os
import sys
import time
from pathlib import Path

import httpx
import yaml
from qdrant_client import models

COLUMNAS = ["pregunta_id", "pregunta", "grupo", "modo", "cache_hit", "tokens_entrada",
            "tokens_salida", "latencia_ms", "category_predicha", "category_real", "modelo"]
RAIZ = Path(__file__).resolve().parent.parent
YAML = Path(__file__).resolve().parent / "preguntas_benchmark.yaml"
CSV_DEFECTO = RAIZ / "data" / "benchmark_grabado.csv"


def cargar_preguntas(ruta: Path = YAML) -> list[dict]:
    """Devuelve las 100 preguntas en orden: originales primero, luego paráfrasis."""
    base = yaml.safe_load(ruta.read_text(encoding="utf-8"))["preguntas"]
    originales = [dict(pregunta_id=b["id"], pregunta=b["pregunta"], grupo="original",
                       category_real=b["category"]) for b in base]
    parafrasis = [dict(pregunta_id=b["id"] + "p", pregunta=b["parafrasis"], grupo="parafrasis",
                       category_real=b["category"]) for b in base]
    return originales + parafrasis


def plan(preguntas: list[dict]) -> list[tuple[dict, str]]:
    """Orden de ejecución: todo con Qdrant (la caché puede acertar) y luego sin Qdrant."""
    return [(p, "con_qdrant") for p in preguntas] + [(p, "sin_qdrant") for p in preguntas]


def fila_de(p: dict, modo: str, r, modelo: str) -> dict:
    return {
        "pregunta_id": p["pregunta_id"], "pregunta": p["pregunta"], "grupo": p["grupo"],
        "modo": modo, "cache_hit": r.cache_hit,
        "tokens_entrada": sum(m.tokens_entrada for m in r.metricas),
        "tokens_salida": sum(m.tokens_salida for m in r.metricas),
        "latencia_ms": round(r.latencia_total_ms(), 1),
        "category_predicha": r.category, "category_real": p["category_real"], "modelo": modelo,
    }


def vaciar_cache() -> None:
    from app.store.cliente import get_client
    from app.store.colecciones import ANSWER_CACHE
    get_client().delete(ANSWER_CACHE, points_selector=models.FilterSelector(filter=models.Filter()),
                        wait=True)


def resumen(ruta: Path, duracion_s: float, fallos: int) -> None:
    filas = list(csv.DictReader(ruta.open(encoding="utf-8")))
    print("\n=== Resumen del benchmark ===")
    print(f"Ollama: {os.environ.get('OLLAMA_URL', '(no definida)')} | "
          f"modelo: {os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')}")
    tot, lat = {}, {}
    for modo in ("con_qdrant", "sin_qdrant"):
        fs = [f for f in filas if f["modo"] == modo]
        tot[modo] = sum(int(f["tokens_entrada"]) + int(f["tokens_salida"]) for f in fs)
        lat[modo] = sum(float(f["latencia_ms"]) for f in fs) / len(fs) if fs else 0.0
        print(f"{modo}: filas={len(fs)} tokens_totales={tot[modo]} latencia_media_ms={lat[modo]:.0f}")
    if tot["sin_qdrant"]:
        ahorro = 100 * (1 - tot["con_qdrant"] / tot["sin_qdrant"])
        print(f"Ahorro de tokens con Qdrant: {ahorro:.1f}%")
    par = [f for f in filas if f["modo"] == "con_qdrant" and f["grupo"] == "parafrasis"]
    aciertos = sum(f["cache_hit"] == "True" for f in par)
    if par:
        print(f"Aciertos de caché en paráfrasis: {aciertos}/{len(par)} ({100 * aciertos / len(par):.1f}%)")
    print(f"Fallos de llamada en esta ejecución: {fallos}")
    print(f"Duración de esta ejecución: {duracion_s / 60:.1f} min")


def main(ruta: Path | None = None) -> int:
    from app.soporte.grafo import responder_con_qdrant, responder_sin_qdrant
    ruta = Path(ruta or os.environ.get("BENCHMARK_PATH") or CSV_DEFECTO)
    modelo = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    hechas: set[tuple[str, str]] = set()
    if ruta.exists() and ruta.stat().st_size > 0:
        with ruta.open(encoding="utf-8") as f:
            hechas = {(x["pregunta_id"], x["modo"]) for x in csv.DictReader(f)}
        print(f"Retomando: {len(hechas)} filas ya escritas")
    else:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with ruta.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, COLUMNAS).writeheader()
        vaciar_cache()
        print("answer_cache vaciada")

    trabajo = plan(cargar_preguntas())
    t0 = time.perf_counter()
    fallos = 0
    for i, (p, modo) in enumerate(trabajo, 1):
        if (p["pregunta_id"], modo) not in hechas:
            try:
                if modo == "con_qdrant":
                    r = responder_con_qdrant(p["pregunta"])
                else:
                    r = responder_sin_qdrant(p["pregunta"])
            except httpx.TimeoutException as e:
                print(f"DETENIDO: una llamada superó el tiempo límite en {p['pregunta_id']} {modo}: {e}")
                return 2
            except Exception as e:  # noqa: BLE001 - se registra el fallo y no se inventan valores
                fallos += 1
                print(f"FALLO {p['pregunta_id']} {modo}: {type(e).__name__}: {e}")
                continue
            with ruta.open("a", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, COLUMNAS).writerow(fila_de(p, modo, r, modelo))
        if i % 10 == 0:
            print(f"[{i}/{len(trabajo)}] {modo} {time.perf_counter() - t0:.0f}s", flush=True)
    resumen(ruta, time.perf_counter() - t0, fallos)
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
