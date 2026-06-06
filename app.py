import streamlit as st

st.set_page_config(page_title="Mapa Interactivo Info UNLP", layout="wide")

pages = [
    st.Page("pages/Inicio.py", title="Inicio", icon="🏠"),
    st.Page("pages/Mapa_interactivo.py", title="Estado del sistema", icon="🗺️"),
    st.Page("pages/Ficha_de_datos.py", title="Ficha de datos") # Oculta
]

