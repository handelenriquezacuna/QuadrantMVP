"""Pestaña 3: denso vs disperso (BM25) vs híbrido (RRF)."""
import streamlit as st

from app.store.busquedas import buscar_denso, buscar_disperso, buscar_hibrido
from app.ui.comun import medir, tabla


def render() -> None:
    st.caption("Qué demuestra: denso y BM25 fallan en casos distintos; "
               "la fusión RRF combina lo mejor de ambos.")
    consulta = st.text_input("Consulta", "refund order 12345", key="t3_consulta")
    if not consulta:
        return
    modos = [("Denso", buscar_denso), ("Disperso (BM25)", buscar_disperso),
             ("Híbrido (RRF)", buscar_hibrido)]
    salidas = [(n, *medir(f, consulta, 5)) for n, f in modos]
    # IDs que aparecen en una sola columna
    conteo: dict = {}
    for _, res, _ in salidas:
        for r in res:
            conteo[r.id] = conteo.get(r.id, 0) + 1
    unicos = {i for i, c in conteo.items() if c == 1}
    st.caption("Las filas marcadas con ★ aparecen en una sola columna.")
    for col, (nombre, res, ms) in zip(st.columns(3), salidas):
        with col:
            st.subheader(nombre)
            st.caption(f"Latencia: {ms:.0f} ms")
            if not res:
                st.info("Sin resultados.")
                continue
            df = tabla(res)
            df.insert(0, "★", ["★" if i in unicos else "" for i in df["id"]])
            st.dataframe(df[["★", "id", "score", "pregunta"]], hide_index=True,
                         use_container_width=True)
