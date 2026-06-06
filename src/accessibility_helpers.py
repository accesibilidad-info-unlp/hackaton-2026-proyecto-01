import streamlit as st

# Opciones para renderizar
_LABELS = {
    "none":            "Ninguno",
    "invert":          "Invertir colores",
    "sat_high":        "Saturación alta",
    "sat_low":         "Saturación baja",
    "mono":            "Monocromático",
    "highlight_links": "Resaltar enlaces",
}

# Notas: hue-rotate invierte sin corrimiento de tonos
# saturate es moderado por las dudas, ajustar de ser necesario
_CSS = {
    "invert": """
        .stApp { filter: invert(1) hue-rotate(180deg); } 
        .stApp img, .stApp video { filter: invert(1) hue-rotate(180deg); }
    """,
    "sat_high":        ".stApp { filter: saturate(3); }",
    "sat_low":         ".stApp { filter: saturate(0.3); }",
    "mono":            ".stApp { filter: saturate(0); }",
    "highlight_links": """
        a, a:visited {
            background: #ffff00 !important;
            color: #000000 !important;
            padding: 0 3px;
            border-radius: 2px;
            font-weight: 700;
            text-decoration: underline !important;
            outline: 2px solid #000000;
        }
    """,
}

# -> es un type hint para saber que tipo devuelve
# None -> no devuelve nada
def color_blindness(option: str) -> None:
    css = _CSS.get(option, "")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_color_blindness_ui() -> str:
    selected = st.radio(
        "Color vision filter",
        options=list(_LABELS.keys()),
        format_func=_LABELS.__getitem__,
        key="cb_option",
        label_visibility="collapsed",
    )
    color_blindness(selected)
    return selected
