import streamlit as st
import pandas as pd
import os

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Mapa Interactivo – Facultad de Informática UNLP",
    layout="wide",
    initial_sidebar_state="auto",
)
# ═══════════════════════════════════════════════════════════════════════════════
# MODOS DE ACCESIBILIDAD VISUAL
# ═══════════════════════════════════════════════════════════════════════════════
#
# Cada modo define una paleta y ajustes de presentación para el mapa y la UI.
#
# MODO 0 – Estándar          : colores por defecto, sin ajustes.
# MODO 1 – Daltonismo        : paleta segura para protanopia/deuteranopia.
#                              Elimina distinción rojo/verde; usa azul/naranja/
#                              amarillo con formas complementarias (patrones).
# MODO 2 – Baja Visión       : alto contraste, tipografía grande, bordes gruesos,
#                              etiquetas siempre visibles en el mapa.
# MODO 3 – Visión Periférica : optimizado para glaucoma / visión tubular.
#                              Elementos grandes centrados, sin información crítica
#                              en los bordes, fuerte foco visual en el centro.
#
VISION_MODES = {
    "Estándar": {
        "id": "standard",
        "icon": "👁",
        "desc": "Visualización por defecto",
        # Colores de tipos de espacio en el mapa
        "colors": {
            "Aula": "#58a6ff",
            "Baño": "#3fb950",
            "Oficina": "#f78166",
            "Lab": "#d2a8ff",
        },
        # Patrones SVG (ninguno en modo estándar)
        "patterns": {
            "Aula": "solid",
            "Baño": "solid",
            "Oficina": "solid",
            "Lab": "solid",
        },
        "font_scale": 1.0,
        "border_width": 1,
        "bg": "#0d1117",
        "surface": "#161b22",
        "text": "#e6edf3",
        "muted": "#7d8590",
        "accent": "#1b6eff",
        "label_always": False,
    },
    "Daltonismo": {
        "id": "colorblind",
        "icon": "◑",
        "desc": "Paleta segura para protanopia / deuteranopia",
        # Paleta Okabe-Ito: universalmente distinguible
        "colors": {
            "Aula": "#0072B2",  # azul
            "Baño": "#E69F00",  # naranja-amarillo
            "Oficina": "#56B4E9",  # celeste
            "Lab": "#F0E442",  # amarillo
        },
        # Patrones diferenciadores además del color
        "patterns": {
            "Aula": "solid",
            "Baño": "diagonal",
            "Oficina": "dots",
            "Lab": "cross",
        },
        "font_scale": 1.0,
        "border_width": 2,
        "bg": "#0d1117",
        "surface": "#161b22",
        "text": "#e6edf3",
        "muted": "#9aa5b4",
        "accent": "#0072B2",
        "label_always": True,
    },
    "Baja Visión": {
        "id": "low_vision",
        "icon": "⊕",
        "desc": "Alto contraste, texto grande, bordes gruesos",
        "colors": {
            "Aula": "#FFFF00",  # amarillo brillante sobre negro
            "Baño": "#00FFFF",  # cian
            "Oficina": "#FF6600",  # naranja intenso
            "Lab": "#FF00FF",  # magenta
        },
        "patterns": {
            "Aula": "solid",
            "Baño": "solid",
            "Oficina": "solid",
            "Lab": "solid",
        },
        "font_scale": 1.45,
        "border_width": 4,
        "bg": "#000000",
        "surface": "#111111",
        "text": "#FFFFFF",
        "muted": "#CCCCCC",
        "accent": "#FFFF00",
        "label_always": True,
    },
    "Visión Periférica": {
        "id": "peripheral",
        "icon": "◎",
        "desc": "Optimizado para glaucoma / visión tubular",
        "colors": {
            "Aula": "#4FC3F7",
            "Baño": "#81C784",
            "Oficina": "#FFB74D",
            "Lab": "#CE93D8",
        },
        "patterns": {
            "Aula": "solid",
            "Baño": "solid",
            "Oficina": "solid",
            "Lab": "solid",
        },
        "font_scale": 1.3,
        "border_width": 3,
        "bg": "#0a0a0a",
        "surface": "#1a1a2e",
        "text": "#F0F0F0",
        "muted": "#AAAAAA",
        "accent": "#4FC3F7",
        "label_always": True,
    },
}

# ── Datos del edificio ───────────────────────────────────────────────────────
FLOORS = {
    "Planta Baja": {
        "file": "assets/datasets/planta_baja_info_UNLP.csv",
        "short": "PB",
    },
    "1er Piso": {
        "file": "assets/datasets/1er_piso_info_UNLP.csv",
        "short": "P1",
    },
    "2do Piso": {
        "file": "assets/datasets/2do_piso_info_UNLP.csv",
        "short": "P2",
    },
}

SPACE_TYPES = ["Aula", "Baño", "Oficina", "Lab"]

# ── Estado de sesión ─────────────────────────────────────────────────────────
if "selected_floor" not in st.session_state:
    st.session_state.selected_floor = "Planta Baja"
if "selected_space" not in st.session_state:
    st.session_state.selected_space = None
if "vision_mode" not in st.session_state:
    st.session_state.vision_mode = "Estándar"

# Alias corto al modo activo
MODE = VISION_MODES[st.session_state.vision_mode]
fs = MODE["font_scale"]  # factor de escala tipográfica


# ═══════════════════════════════════════════════════════════════════════════════
# CSS DINÁMICO (se regenera en cada cambio de modo)
# ═══════════════════════════════════════════════════════════════════════════════
def build_css(mode: dict) -> str:
    bg = mode["bg"]
    surf = mode["surface"]
    text = mode["text"]
    muted = mode["muted"]
    accent = mode["accent"]
    bw = mode["border_width"]
    fs = mode["font_scale"]

    # Tamaños tipográficos escalados
    t_body = f"{0.82 * fs:.2f}rem"
    t_small = f"{0.72 * fs:.2f}rem"
    t_mono = f"{0.78 * fs:.2f}rem"
    t_h1 = f"{1.9  * fs:.2f}rem"

    extra = ""
    # Modo baja visión: vignette interna para facilitar foco
    if mode["id"] == "low_vision":
        extra += """
        .map-panel::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 10px;
            box-shadow: inset 0 0 0 6px #FFFF0044;
            pointer-events: none;
        }"""
    # Modo visión periférica: vignette oscura en bordes del mapa
    if mode["id"] == "peripheral":
        extra += """
        .map-panel::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 10px;
            background: radial-gradient(ellipse 60% 55% at 50% 50%,
                transparent 55%, rgba(0,0,0,0.75) 100%);
            pointer-events: none;
        }"""

    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'IBM Plex Sans', sans-serif;
        font-size: {t_body};
    }}
    .stApp {{
        background-color: {bg};
        color: {text};
    }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }}

    /* ── Header ── */
    .map-header {{
        border-bottom: {bw}px solid {accent}44;
        padding-bottom: 1.2rem;
        margin-bottom: 1.8rem;
    }}
    .map-header .eyebrow {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        letter-spacing: 0.18em;
        color: {accent};
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .map-header h1 {{
        font-size: {t_h1};
        font-weight: 600;
        color: {text};
        margin: 0;
        line-height: 1.2;
    }}
    .map-header .subtitle {{
        font-size: {t_body};
        color: {muted};
        margin-top: 0.3rem;
    }}

    /* ── Selector de pisos ── */
    .floor-selector-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        letter-spacing: 0.12em;
        color: {muted};
        text-transform: uppercase;
        margin-bottom: 0.4rem;
    }}
    div.stRadio > div[role="radiogroup"] {{
        display: flex;
        flex-direction: row;
        gap: 0.5rem;
        flex-wrap: wrap;
    }}
    div.stRadio > div[role="radiogroup"] > label {{
        background: {surf};
        border: {bw}px solid {muted}66;
        border-radius: 6px;
        padding: 0.45rem 1.1rem;
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        color: {muted};
        cursor: pointer;
        transition: all 0.15s ease;
    }}
    div.stRadio > div[role="radiogroup"] > label:hover {{
        border-color: {accent};
        color: {text};
    }}
    div.stRadio > div[role="radiogroup"] > label[data-checked="true"],
    div.stRadio > div[role="radiogroup"] > label[aria-checked="true"] {{
        background: {accent}22;
        border-color: {accent};
        color: {accent};
        font-weight: 600;
    }}

    /* ── Panel del mapa ── */
    .map-panel {{
        background: {surf};
        border: {bw}px solid {accent}44;
        border-radius: 10px;
        overflow: hidden;
        position: relative;
    }}
    .map-panel-header {{
        background: {bg};
        border-bottom: {bw}px solid {accent}33;
        padding: 0.75rem 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }}
    .map-panel-header .floor-badge {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        color: {accent};
        background: {accent}22;
        border: {bw}px solid {accent}44;
        border-radius: 4px;
        padding: 0.15rem 0.6rem;
        margin-left: auto;
        font-weight: 600;
    }}
    .map-placeholder {{
        min-height: 480px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        gap: 1rem;
    }}
    .map-placeholder p {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        color: {muted};
        margin: 0;
    }}

    /* ── Selector de modo de accesibilidad ── */
    .a11y-bar {{
        display: flex;
        align-items: center;
        gap: 0.8rem;
        background: {surf};
        border: {bw}px solid {accent}33;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }}
    .a11y-bar .a11y-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        color: {muted};
        letter-spacing: 0.1em;
        text-transform: uppercase;
        white-space: nowrap;
    }}

    /* ── Info cards ── */
    .info-card {{
        background: {surf};
        border: {bw}px solid {accent}33;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.8rem;
    }}
    .info-card .card-title {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_small};
        letter-spacing: 0.1em;
        color: {muted};
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }}
    .stat-row {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.3rem 0;
        border-bottom: 1px solid {accent}22;
        font-size: {t_body};
    }}
    .stat-row:last-child {{ border-bottom: none; }}
    .stat-row .stat-label {{ color: {muted}; }}
    .stat-row .stat-val {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {t_mono};
        color: {accent};
        font-weight: 600;
    }}

    /* ── Leyenda ── */
    .legend-item {{
        display: flex;
        align-items: center;
        gap: 0.6rem;
        padding: 0.32rem 0;
        font-size: {t_body};
        color: {text};
        border-bottom: 1px solid {accent}11;
    }}
    .legend-item:last-child {{ border-bottom: none; }}
    .legend-swatch {{
        width: {int(14 * fs)}px;
        height: {int(14 * fs)}px;
        border-radius: 3px;
        border: {bw}px solid #ffffff33;
        flex-shrink: 0;
    }}
    .legend-pattern-label {{
        font-family: 'IBM Plex Mono', monospace;
        font-size: {0.65 * fs:.2f}rem;
        color: {muted};
        margin-left: auto;
    }}

    /* ── Barra de búsqueda ── */
    .stTextInput input {{
        background: {surf} !important;
        border: {bw}px solid {muted}66 !important;
        border-radius: 6px !important;
        color: {text} !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: {t_body} !important;
    }}
    .stTextInput input:focus {{
        border-color: {accent} !important;
        box-shadow: 0 0 0 3px {accent}22 !important;
    }}
    .stTextInput input::placeholder {{ color: {muted}88 !important; }}

    /* ── Nota de accesibilidad activa ── */
    .a11y-notice {{
        background: {accent}18;
        border-left: {bw * 2}px solid {accent};
        border-radius: 0 6px 6px 0;
        padding: 0.6rem 0.9rem;
        font-size: {t_small};
        color: {text};
        margin-bottom: 0.8rem;
        line-height: 1.5;
    }}

    {extra}
</style>
"""


st.markdown(build_css(MODE), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GENERADOR DE MAPA SVG (placeholder con lógica de accesibilidad lista)
# ═══════════════════════════════════════════════════════════════════════════════
def build_map_svg(floor: str, mode: dict) -> str:
    """
    Genera un SVG de placeholder que ya implementa la lógica de accesibilidad:
    colores por modo, patrones para daltonismo, tamaños para baja visión, etc.
    Cuando se integre el plano real, esta función recibe el mismo 'mode' dict
    y aplica los mismos ajustes al SVG real.
    """
    colors = mode["colors"]
    patterns = mode["patterns"]
    bw = mode["border_width"]
    fs = mode["font_scale"]
    la = mode["label_always"]  # siempre mostrar etiqueta
    surf = mode["surface"]
    muted = mode["muted"]
    accent = mode["accent"]

    label_size = int(11 * fs)
    rect_stroke = bw

    # Definiciones de patrones SVG para modo daltonismo
    defs = """<defs>
        <pattern id="pat_diagonal" patternUnits="userSpaceOnUse" width="8" height="8" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(255,255,255,0.35)" stroke-width="3"/>
        </pattern>
        <pattern id="pat_dots" patternUnits="userSpaceOnUse" width="8" height="8">
            <circle cx="4" cy="4" r="1.8" fill="rgba(255,255,255,0.4)"/>
        </pattern>
        <pattern id="pat_cross" patternUnits="userSpaceOnUse" width="10" height="10">
            <line x1="0" y1="5" x2="10" y2="5" stroke="rgba(255,255,255,0.35)" stroke-width="2"/>
            <line x1="5" y1="0" x2="5"  y2="10" stroke="rgba(255,255,255,0.35)" stroke-width="2"/>
        </pattern>
        <filter id="blur_vignette">
            <feGaussianBlur stdDeviation="0"/>
        </filter>
    </defs>"""

    pat_map = {
        "solid": None,
        "diagonal": "url(#pat_diagonal)",
        "dots": "url(#pat_dots)",
        "cross": "url(#pat_cross)",
    }

    # Celdas de ejemplo: (tipo, x, y, w, h, nombre)
    sample_rooms = [
        ("Aula", 30, 40, 130, 90, "Aula 1"),
        ("Aula", 180, 40, 130, 90, "Aula 2"),
        ("Lab", 330, 40, 160, 90, "Lab A"),
        ("Baño", 30, 160, 60, 70, "Baño"),
        ("Oficina", 110, 160, 150, 70, "Secretaría"),
        ("Aula", 280, 160, 130, 70, "Aula 3"),
        ("Lab", 430, 160, 100, 70, "Lab B"),
        ("Oficina", 30, 260, 200, 80, "Dirección"),
        ("Baño", 250, 260, 60, 80, "Baño 2"),
        ("Aula", 330, 260, 200, 80, "Aula 4"),
    ]

    rooms_svg = []
    for tipo, x, y, w, h, nombre in sample_rooms:
        color = colors.get(tipo, "#888")
        pat_key = patterns.get(tipo, "solid")
        pat_url = pat_map.get(pat_key)

        # Rectángulo base con color
        rooms_svg.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'rx="4" fill="{color}33" '
            f'stroke="{color}" stroke-width="{rect_stroke}"/>'
        )
        # Capa de patrón encima (daltonismo)
        if pat_url:
            rooms_svg.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'rx="4" fill="{pat_url}" opacity="0.7"/>'
            )
        # Etiqueta de tipo (pequeña, arriba)
        tipo_y = y + label_size + 4
        rooms_svg.append(
            f'<text x="{x + w//2}" y="{tipo_y}" '
            f'text-anchor="middle" font-size="{label_size - 2}" '
            f'font-family="IBM Plex Mono" fill="{color}" font-weight="600">'
            f"{tipo}</text>"
        )
        # Nombre del espacio (siempre visible en modos accesibles)
        if la or True:
            nombre_y = y + h // 2 + label_size // 2 + 4
            rooms_svg.append(
                f'<text x="{x + w//2}" y="{nombre_y}" '
                f'text-anchor="middle" font-size="{label_size}" '
                f'font-family="IBM Plex Sans" fill="{muted}" font-weight="400">'
                f"{nombre}</text>"
            )

    # Indicador de piso
    floor_text = (
        f'<text x="550" y="380" text-anchor="end" '
        f'font-size="{int(11 * fs)}" font-family="IBM Plex Mono" '
        f'fill="{accent}" opacity="0.6">{floor} · placeholder</text>'
    )

    rooms_joined = "\n        ".join(rooms_svg)

    return f"""
    <svg viewBox="0 0 560 400" xmlns="http://www.w3.org/2000/svg"
         style="width:100%;height:100%;display:block;">
        {defs}
        <!-- Fondo del plano -->
        <rect width="560" height="400" fill="{surf}" rx="2"/>
        <!-- Paredes perimetrales -->
        <rect x="20" y="20" width="520" height="360" rx="6"
              fill="none" stroke="{accent}33" stroke-width="{bw + 1}"/>
        <!-- Espacios -->
        {rooms_joined}
        {floor_text}
    </svg>
    """


# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_floor_data(filepath: str):
    if os.path.exists(filepath):
        return pd.read_csv(filepath)
    return None


def get_floor_stats(df) -> dict:
    if df is None:
        return {}
    if "tipo" in df.columns:
        return df["tipo"].value_counts().to_dict()
    return {}


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
col_map, col_info = st.columns([3, 1], gap="large")

with col_map:
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        f"""
    <div class="map-header">
        <div class="eyebrow">Facultad de Informática · UNLP</div>
        <h1>Mapa Interactivo</h1>
        <div class="subtitle">Navegá por las instalaciones del edificio</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Barra de accesibilidad ───────────────────────────────────────────────
    st.markdown(
        f'<div class="a11y-bar"><span class="a11y-label">Modo visual</span></div>',
        unsafe_allow_html=True,
    )

    vision_mode = st.radio(
        label="Modo de visión",
        options=list(VISION_MODES.keys()),
        index=list(VISION_MODES.keys()).index(st.session_state.vision_mode),
        horizontal=True,
        label_visibility="collapsed",
        key="vision_radio",
        format_func=lambda k: f"{VISION_MODES[k]['icon']}  {k}",
    )

    # Si cambió el modo, refrescar
    if vision_mode != st.session_state.vision_mode:
        st.session_state.vision_mode = vision_mode
        st.rerun()

    # Nota descriptiva del modo activo
    if MODE["id"] != "standard":
        descriptions = {
            "colorblind": (
                "🎨  <b>Modo Daltonismo</b>: paleta Okabe-Ito, segura para protanopia y deuteranopia. "
                "Cada tipo de espacio también se distingue por un patrón visual (rayas, puntos, cruces)."
            ),
            "low_vision": (
                "⊕  <b>Modo Baja Visión</b>: máximo contraste (negro/amarillo), tipografía ampliada "
                "y bordes reforzados para facilitar la lectura en todo momento."
            ),
            "peripheral": (
                "◎  <b>Modo Visión Periférica</b>: elementos de gran tamaño centrados en pantalla, "
                "vignette oscura en los bordes para concentrar la atención en el área central del mapa."
            ),
        }
        st.markdown(
            f'<div class="a11y-notice">' f'{descriptions[MODE["id"]]}' f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    # ── Selector de pisos ────────────────────────────────────────────────────
    st.markdown(
        '<div class="floor-selector-label">Seleccionar piso</div>',
        unsafe_allow_html=True,
    )
    selected_floor = st.radio(
        label="piso",
        options=list(FLOORS.keys()),
        index=list(FLOORS.keys()).index(st.session_state.selected_floor),
        horizontal=True,
        label_visibility="collapsed",
        key="floor_radio",
    )
    st.session_state.selected_floor = selected_floor

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Panel del mapa ───────────────────────────────────────────────────────
    floor_meta = FLOORS[selected_floor]
    map_svg = build_map_svg(selected_floor, MODE)

    st.markdown(
        f"""
    <div class="map-panel">
        <div class="map-panel-header">
            <span style="font-family:'IBM Plex Mono',monospace;
                         font-size:{0.7 * fs:.2f}rem;
                         color:{MODE['muted']}">
                {MODE['icon']} Modo {st.session_state.vision_mode}
            </span>
            <span class="floor-badge">{floor_meta['short']} · {selected_floor}</span>
        </div>
        <div style="padding:1rem;">
            {map_svg}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


with col_info:
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    # ── Búsqueda ─────────────────────────────────────────────────────────────
    search_query = st.text_input(
        label="buscar",
        placeholder="🔍  Buscar aula, oficina…",
        label_visibility="collapsed",
    )

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Stats ────────────────────────────────────────────────────────────────
    df = load_floor_data(floor_meta["file"])
    stats = get_floor_stats(df)
    total = sum(stats.values()) if stats else "—"

    st.markdown(
        f"""
    <div class="info-card">
        <div class="card-title">Estadísticas · {selected_floor}</div>
        <div class="stat-row">
            <span class="stat-label">Total espacios</span>
            <span class="stat-val">{total}</span>
        </div>
        {"".join(
            f'<div class="stat-row"><span class="stat-label">{k}</span>'
            f'<span class="stat-val">{v}</span></div>'
            for k, v in stats.items()
        ) if stats else
        '<div class="stat-row"><span class="stat-label" style="font-style:italic;font-size:0.75rem">Dataset no cargado</span></div>'
        }
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Leyenda adaptada al modo ──────────────────────────────────────────────
    pattern_labels = {
        "solid": "",
        "diagonal": "rayas",
        "dots": "puntos",
        "cross": "cruces",
    }

    legend_items = []
    for tipo in SPACE_TYPES:
        color = MODE["colors"].get(tipo, "#888")
        pat_key = MODE["patterns"].get(tipo, "solid")
        pat_lbl = pattern_labels.get(pat_key, "")
        legend_items.append(
            f'<div class="legend-item">'
            f'<div class="legend-swatch" style="background:{color};"></div>'
            f"<span>{tipo}</span>"
            f'{"<span class=legend-pattern-label>" + pat_lbl + "</span>" if pat_lbl else ""}'
            f"</div>"
        )

    st.markdown(
        f"""
    <div class="info-card">
        <div class="card-title">Leyenda</div>
        {"".join(legend_items)}
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Espacio seleccionado ──────────────────────────────────────────────────
    st.markdown(
        f"""
    <div class="info-card" style="opacity:0.6;">
        <div class="card-title">Espacio seleccionado</div>
        <div style="font-family:'IBM Plex Mono',monospace;
                    font-size:{0.72 * fs:.2f}rem;
                    color:{MODE['muted']};
                    padding:0.5rem 0;">
            Hacé clic en el mapa para ver detalles
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )
