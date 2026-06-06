import streamlit as st
import sys
from pathlib import Path

# Configuración de la ruta para importar módulos visuales (como la sidebar)
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "visuals"))

# Intento de importar la sidebar (asegurate de tener el archivo creado)
try:
    from sidebar import mostrar_sidebar

    mostrar_sidebar()
except ImportError:
    pass

st.title("Inicio")

# Título principal de la app
st.title("🗺️ InfoMap UNLP - Mapa Interactivo")

st.write(
    "¡Bienvenido a la plataforma de navegación y gestión de espacios de la Facultad de Informática de la UNLP! "
    "Esta aplicación permite explorar y ubicar de manera interactiva cada rincón del edificio, recorriendo sus tres niveles: Planta Baja, 1º Piso y 2º Piso."
)

st.write(
    "Contar con un sistema de mapeo centralizado es fundamental para mejorar la experiencia de estudiantes, "
    "docentes, no docentes y visitantes. Permite encontrar rápidamente aulas y oficinas, optimizar la movilidad "
    "dentro de la facultad y conocer en tiempo real los recursos disponibles en cada sala."
)

st.subheader("¿Qué información contiene el mapa?")

st.write(
    "El sistema cuenta con un relevamiento estructurado de los 53 espacios de la facultad. "
    "Dentro de la plataforma podrás consultar información como:"
)

st.write(
    "- **Espacios Mapeados:** Aulas de cursada, áreas administrativas, laboratorios y centros de investigación (LIFIA, LINTI, III-LIDI), baños, buffet, fotocopiadora y biblioteca.\n"
    "- **Infraestructura:** Capacidad aproximada de cada lugar y disponibilidad de proyector/pantalla.\n"
    "- **Actividad:** Cátedras asignadas a cada aula e investigadores/personal responsable a cargo.\n"
    "- **Disponibilidad:** Estado actual del espacio (Disponible, Ocupado, En Mantenimiento)."
)

st.subheader("Cómo usar la aplicación")

st.write(
    "Usá el menú de la barra lateral izquierda para navegar entre las distintas secciones:"
)

st.write("- **Inicio**: Descripción general de la aplicación y manual de uso.")
st.write(
    "- **Mapa Interactivo**: Explorá visualmente cada piso de la facultad. Podés interactuar con los distintos espacios para ver su ficha de información detallada."
)
st.write(
    "- **Directorio de Espacios / Datos**: Accedé a la tabla completa con la base de datos de la facultad para filtrar rápidamente por tipo de espacio, piso o disponibilidad."
)

st.markdown("---")
st.caption(
    "🚀 Proyecto desarrollado para la Hackatón 2026 - Facultad de Informática, UNLP."
)
