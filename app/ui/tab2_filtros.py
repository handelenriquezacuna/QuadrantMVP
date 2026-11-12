"""Pestaña 2: búsqueda densa con filtros de payload frente a sin filtro."""
import streamlit as st

from app.store.busquedas import buscar_denso, listar_valores
from app.ui.comun import medir, mostrar


def render() -> None:
    st.caption("Qué demuestra: los filtros de payload acotan la búsqueda vectorial "
               "sin perder el orden por similitud.")
    consulta = st.text_input("Consulta", "no puedo acceder a mi cuenta", key="t2_consulta")
    categorias = listar_valores("category")
    c1, c2 = st.columns(2)
    categoria = c1.selectbox("category", ["(todas)"] + categorias, key="t2_cat")
    cat = None if categoria == "(todas)" else categoria
    intents = listar_valores("intent", cat)
    intent_sel = c2.selectbox("intent", ["(todos)"] + intents, key="t2_intent")
    intent = None if intent_sel == "(todos)" else intent_sel
    if not consulta:
        return
    col1, col2 = st.columns(2)
    with col1:
        res, ms = medir(buscar_denso, consulta, 5, cat, intent)
        mostrar("Con filtro", res, ms)
    with col2:
        res, ms = medir(buscar_denso, consulta, 5)
        mostrar("Sin filtro", res, ms)
