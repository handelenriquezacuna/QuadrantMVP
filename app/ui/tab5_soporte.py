"""Pestaña 5: asistente de soporte con y sin Qdrant, y benchmark grabado."""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from app.soporte import grafo, metricas, ollama
from app.store import busquedas
from app.ui.comun import medir

COLUMNAS = ["pregunta_id", "pregunta", "grupo", "modo", "cache_hit", "tokens_entrada",
            "tokens_salida", "latencia_ms", "category_predicha", "category_real", "modelo"]


def _ruta_benchmark() -> Path:
    return Path(os.environ.get("BENCHMARK_PATH") or "data/benchmark_grabado.csv")


def cargar_benchmark() -> pd.DataFrame | None:
    """Lee el CSV grabado; devuelve None si falta o no tiene las columnas esperadas."""
    ruta = _ruta_benchmark()
    if not ruta.exists():
        return None
    try:
        df = pd.read_csv(ruta)
    except Exception:  # noqa: BLE001
        return None
    if not set(COLUMNAS).issubset(df.columns):
        return None
    df["cache_hit"] = df["cache_hit"].astype(str).str.lower().isin(["true", "1"])
    return df


def _porcentaje_ahorro(sin: float, con: float) -> float:
    return (1 - con / sin) * 100 if sin else 0.0


def _referencias() -> list[str]:
    return list(metricas.cargar_precios())


def _graficos_benchmark(referencia: str) -> None:
    """KPIs y gráficos del benchmark grabado."""
    st.subheader("Benchmark grabado")
    df = cargar_benchmark()
    if df is None:
        st.warning(f"No se encontró un benchmark válido en {_ruta_benchmark()}. "
                   "Genéralo con `python -m ingest.benchmark` (Ollama en el host).")
        return
    df["tokens"] = df["tokens_entrada"] + df["tokens_salida"]
    df["costo_usd"] = [metricas.costo_usd(int(e), int(s), referencia)
                       for e, s in zip(df["tokens_entrada"], df["tokens_salida"])]
    por_modo = df.groupby("modo").agg(
        tokens=("tokens", "mean"), latencia_ms=("latencia_ms", "mean"),
        costo_usd=("costo_usd", "mean"), cache=("cache_hit", "mean"))
    con = por_modo["tokens"].get("con_qdrant", 0.0)
    sin = por_modo["tokens"].get("sin_qdrant", 0.0)
    df_con = df[df["modo"] == "con_qdrant"]
    para = df_con[df_con["grupo"] == "parafrasis"]
    exacta = (df["category_predicha"] == df["category_real"]).groupby(df["modo"]).mean() * 100
    k = st.columns(4)
    k[0].metric("Tokens medios con / sin", f"{con:.0f} / {sin:.0f}")
    k[1].metric("Ahorro de tokens", f"{_porcentaje_ahorro(sin, con):.1f} %")
    k[2].metric("Caché en paráfrasis", f"{int(para['cache_hit'].sum())} / {len(para)}")
    k[3].metric("Categoría correcta con / sin",
                f"{exacta.get('con_qdrant', 0):.0f} % / {exacta.get('sin_qdrant', 0):.0f} %")
    st.caption(f"{len(df)} corridas · tokens totales con / sin: "
               f"{int(df_con['tokens'].sum()):,} / {int(df[df['modo'] == 'sin_qdrant']['tokens'].sum()):,} · "
               f"costo total USD ({referencia}): {df['costo_usd'].sum():.4f}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Tokens medios por modo")
        st.bar_chart(por_modo["tokens"])
    with c2:
        st.caption("Latencia media (ms) por modo")
        st.bar_chart(por_modo["latencia_ms"])
    with c3:
        st.caption("Costo medio USD por consulta")
        st.bar_chart(por_modo["costo_usd"])
    st.caption("Tasa de aciertos de caché (%) por grupo, con Qdrant")
    cache = df[df["modo"] == "con_qdrant"].groupby("grupo")["cache_hit"].mean() * 100
    st.bar_chart(cache)


def _tabla_nodos(res) -> pd.DataFrame:
    return pd.DataFrame([{"nodo": m.nodo, "tokens_entrada": m.tokens_entrada,
                          "tokens_salida": m.tokens_salida,
                          "latencia_ms": round(m.latencia_ms, 1), "cache_hit": m.cache_hit}
                         for m in res.metricas])


def _modo_en_vivo(referencia: str) -> None:
    st.subheader("Consulta en vivo")
    c1, c2 = st.columns([3, 1])
    try:
        if c2.button("Vaciar caché", key="t5_vaciar"):
            n = busquedas.cache_vaciar()
            st.session_state.pop("t5_res", None)
            st.toast(f"Caché vaciada: {n} respuestas borradas.")
        c1.caption(f"Respuestas en caché semántica: {busquedas.cache_contar()} "
                   f"(umbral {os.environ.get('CACHE_THRESHOLD', '0.92')})")
    except Exception as e:  # noqa: BLE001
        c1.caption(f"No se pudo leer la caché: {e}")
    pregunta = st.text_input("Pregunta del cliente", key="t5_pregunta")
    if st.button("Consultar en ambos modos", key="t5_consultar") and pregunta.strip():
        try:
            con, ms_con = medir(grafo.responder_con_qdrant, pregunta)
            sin, ms_sin = medir(grafo.responder_sin_qdrant, pregunta)
            st.session_state["t5_res"] = (con, ms_con, sin, ms_sin)
        except Exception as e:  # noqa: BLE001
            st.error(f"Falló la consulta: {e}")
            return
    if "t5_res" not in st.session_state:
        return
    con, ms_con, sin, ms_sin = st.session_state["t5_res"]
    cols = st.columns(2)
    for col, titulo, res, ms in ((cols[0], "Con Qdrant", con, ms_con),
                                 (cols[1], "Sin Qdrant", sin, ms_sin)):
        with col:
            st.markdown(f"**{titulo}**")
            st.caption(f"Latencia: {ms:.0f} ms · categoría: {res.category} · "
                       f"caché: {'sí' if res.cache_hit else 'no'}")
            st.write(res.respuesta)
            st.dataframe(_tabla_nodos(res), hide_index=True, use_container_width=True)
    tc, ts = con.tokens_totales(), sin.tokens_totales()
    costo = lambda r: sum(metricas.costo_usd(m.tokens_entrada, m.tokens_salida, referencia)  # noqa: E731
                          for m in r.metricas)
    k = st.columns(5)
    k[0].metric("Tokens con Qdrant", tc, delta=tc - ts, delta_color="inverse")
    k[1].metric("Ahorro de tokens", f"{_porcentaje_ahorro(ts, tc):.1f} %")
    k[2].metric("Caché", "acierto" if con.cache_hit else "fallo")
    k[3].metric("Latencia con / sin (ms)", f"{con.latencia_total_ms():.0f} / {sin.latencia_total_ms():.0f}")
    k[4].metric("Costo USD con / sin", f"{costo(con):.6f} / {costo(sin):.6f}")


def render() -> None:
    st.caption("Qué demuestra: el asistente con y sin Qdrant, y el ahorro de tokens "
               "gracias a la recuperación y a la caché semántica.")
    referencias = _referencias()
    referencia = st.selectbox("Precio de referencia", referencias, key="t5_ref") if referencias else None
    if referencia is None:
        st.error("No hay modelos de referencia en pricing.yaml.")
        return
    if ollama.disponible():
        _modo_en_vivo(referencia)
    else:
        st.warning("Ollama no está disponible: se muestran solo los resultados del benchmark grabado.")
    _graficos_benchmark(referencia)
