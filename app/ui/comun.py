"""Utilidades compartidas por las pestañas: medición de latencia y tablas de resultados."""
import time

import pandas as pd
import streamlit as st


def medir(funcion, *args, **kwargs):
    """Ejecuta la función y devuelve (resultado, latencia en ms)."""
    inicio = time.perf_counter()
    resultado = funcion(*args, **kwargs)
    return resultado, (time.perf_counter() - inicio) * 1000


def tabla(resultados) -> pd.DataFrame:
    """Convierte una lista de Resultado en un DataFrame legible."""
    return pd.DataFrame([
        {"id": r.id, "score": round(r.score, 4), "pregunta": r.instruction,
         "categoría": r.category, "intent": r.intent}
        for r in resultados
    ])


def mostrar(titulo: str, resultados, ms: float) -> None:
    """Muestra una columna con título, latencia y tabla de resultados."""
    st.subheader(titulo)
    st.caption(f"Latencia: {ms:.0f} ms")
    if resultados:
        st.dataframe(tabla(resultados), hide_index=True, use_container_width=True)
    else:
        st.info("Sin resultados.")
