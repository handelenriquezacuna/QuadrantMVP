"""Pestaña 4: recomendaciones por ejemplos positivos y negativos."""
import streamlit as st

from app.store.busquedas import buscar_denso, recomendar
from app.ui.comun import medir, mostrar


def render() -> None:
    st.caption("Qué demuestra: la API de recomendación encuentra puntos parecidos "
               "a unos ejemplos y alejados de otros, sin escribir consulta.")
    consulta = st.text_input("Buscar ejemplos", "devolver un producto", key="t4_consulta")
    candidatos = buscar_denso(consulta, 10) if consulta else []
    opciones = {r.id: f"{r.id} · {r.instruction[:70]}" for r in candidatos}
    positivos = st.multiselect("Ejemplos positivos", list(opciones), format_func=opciones.get,
                               key="t4_pos")
    negativos = st.multiselect("Ejemplos negativos", list(opciones), format_func=opciones.get,
                               key="t4_neg")
    estrategia = st.radio("Estrategia", ["average_vector", "best_score"], horizontal=True,
                          key="t4_estrategia")
    if not positivos:
        st.info("Elige al menos un ejemplo positivo.")
        return
    res, ms = medir(recomendar, positivos, negativos, 5, estrategia)
    mostrar("Recomendaciones", res, ms)
