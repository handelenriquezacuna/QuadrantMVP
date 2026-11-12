"""Punto de entrada Streamlit: seis pestañas del laboratorio Qdrant."""
import streamlit as st

from app.ui import (tab1_semantica, tab2_filtros, tab3_hibrida,
                    tab4_recomendaciones, tab5_soporte, tab6_inspector)

st.set_page_config(layout="wide", page_title="Qdrant Lab")
st.title("Qdrant Lab")

NOMBRES = ["1 Semántica", "2 Filtros", "3 Híbrida", "4 Recomendaciones", "5 Soporte", "6 Inspector"]
MODULOS = [tab1_semantica, tab2_filtros, tab3_hibrida, tab4_recomendaciones,
           tab5_soporte, tab6_inspector]

for pestana, modulo in zip(st.tabs(NOMBRES), MODULOS):
    with pestana:
        modulo.render()
