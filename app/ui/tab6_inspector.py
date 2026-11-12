"""Pestaña 6: inspector de colecciones y prueba de la API key."""
import os

import streamlit as st

from app.store.cliente import probar_api_key
from app.store.colecciones import ANSWER_CACHE, FAQ_KB, info_coleccion, listar_colecciones
from app.ui.comun import medir


def render() -> None:
    st.caption("Qué demuestra: configuración interna de las colecciones (HNSW, cuantización, "
               "memoria) y que Qdrant rechaza peticiones sin API key.")
    info, ms = medir(lambda: {n: info_coleccion(n) for n in (FAQ_KB, ANSWER_CACHE)})
    st.caption(f"Latencia: {ms:.0f} ms")
    st.write("Colecciones:", ", ".join(listar_colecciones()))
    cols = st.columns(2)
    for col, (nombre, d) in zip(cols, info.items()):
        with col:
            st.subheader(nombre)
            st.metric("Puntos", d["puntos"])
            st.write(f"Segmentos: {d['segmentos']} · Estado: {d['estado']}")
            st.write("HNSW"); st.json(d["hnsw"])
            st.write("Cuantización"); st.json(d["cuantizacion"] or {"cuantizacion": "ninguna"})
            mem = d["memoria_estimada_mb"]
            st.write(f"Memoria estimada: float32 {mem['float32']:.1f} MB vs int8 {mem['int8']:.1f} MB")
    url = os.environ.get("QDRANT_URL_PUBLICA", "http://localhost:6333")
    st.link_button("Abrir dashboard de Qdrant", f"{url}/dashboard")
    st.divider()
    if st.button("Probar API key", key="t6_probar"):
        r = probar_api_key()
        c1, c2, c3 = st.columns(3)
        c1.metric("Sin clave", r["sin_clave"])
        c2.metric("Clave incorrecta", r["clave_incorrecta"])
        c3.metric("Con clave", r["con_clave"])
        if r["sin_clave"] in (401, 403) and r["con_clave"] == 200:
            st.success("Qdrant rechaza sin clave (401/403) y acepta con clave (200).")
        else:
            st.error("Comportamiento inesperado de la API key.")
