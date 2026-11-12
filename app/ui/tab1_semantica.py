"""Pestaña 1: búsqueda semántica (densa) frente a búsqueda por palabra exacta."""
import streamlit as st

from app.store.busquedas import buscar_denso, buscar_palabra_exacta
from app.ui.comun import medir, mostrar


def render() -> None:
    st.caption("Qué demuestra: el vector denso encuentra significado aunque no compartas palabras; "
               "la palabra exacta solo acierta si el texto la contiene.")
    consulta = st.text_input("Consulta", "quiero cancelar mi pedido", key="t1_consulta")
    if not consulta:
        return
    col1, col2 = st.columns(2)
    with col1:
        res, ms = medir(buscar_denso, consulta, 5)
        mostrar("Semántica (denso)", res, ms)
    with col2:
        res, ms = medir(buscar_palabra_exacta, consulta, 5)
        mostrar("Palabra exacta", res, ms)
