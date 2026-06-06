# utilidades para la carga y procesamiento de los datasets
import pandas as pd
import streamlit as st
from pathlib import Path

# ruta base a los datasets (relativa a este archivo)
DATASET_PATH = Path(__file__).parent.parent.parent / "assets" / "datasets"

# archivos csv por piso
ARCHIVOS_PISO = {
    "Planta Baja": "planta_baja_info_UNLP.csv",
    "1er Piso": "1er_piso_info_UNLP.csv",
    "2do Piso": "2do_piso_info_UNLP.csv",
}


@st.cache_data
def cargar_dataset_completo() -> pd.DataFrame:
    """
    lee los 3 csvs por piso, los unifica en un unico dataframe
    y aplica limpieza y normalizacion de tipos.
    """
    frames = []

    for piso, archivo in ARCHIVOS_PISO.items():
        ruta = DATASET_PATH / archivo
        df_piso = pd.read_csv(ruta, dtype={"idMapa": str})
        # aseguramos que la columna piso coincida con la clave
        df_piso["piso"] = piso
        frames.append(df_piso)

    df = pd.concat(frames, ignore_index=True)
    df = _limpiar_datos(df)
    return df


def _limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """
    normaliza tipos y agrega un id unico global para cada espacio.
    """
    # --- id unico global (evita colisiones entre pisos) ---
    df = df.reset_index(drop=True)
    df.insert(0, "id_global", range(1, len(df) + 1))

    # --- capacidad: rellenar vacios con 0 y convertir a int ---
    df["capacidad"] = pd.to_numeric(df["capacidad"], errors="coerce").fillna(0).astype(int)

    # --- proyector: normalizar a booleano ---
    df["tieneProyector"] = df["tieneProyector"].astype(str).str.upper().map(
        {"TRUE": True, "FALSE": False}
    ).fillna(False)

    # --- estado: limpiar espacios en blanco ---
    df["estadoActual"] = df["estadoActual"].str.strip()

    # --- catedras: rellenar vacios ---
    df["catedrasAsignadas"] = df["catedrasAsignadas"].fillna("Sin asignar")

    # --- responsable: rellenar vacios ---
    df["responsable"] = df["responsable"].fillna("Sin asignar")

    # --- idmapa: limpiar espacios ---
    df["idMapa"] = df["idMapa"].str.strip()

    return df


# ---------------------------------------------------------------------------
# funciones de filtrado
# ---------------------------------------------------------------------------

def filtrar_por_piso(df: pd.DataFrame, piso: str) -> pd.DataFrame:
    """filtra el dataframe por piso."""
    return df[df["piso"] == piso].copy()


def filtrar_por_tipo(df: pd.DataFrame, tipo: str) -> pd.DataFrame:
    """filtra el dataframe por tipo de espacio."""
    return df[df["tipoEspacio"] == tipo].copy()


def filtrar_por_estado(df: pd.DataFrame, estado: str) -> pd.DataFrame:
    """filtra el dataframe por estado actual."""
    return df[df["estadoActual"] == estado].copy()


# ---------------------------------------------------------------------------
# busqueda inteligente
# ---------------------------------------------------------------------------

def buscar_espacios(
    df: pd.DataFrame,
    capacidad_min: int = 0,
    proyector: bool | None = None,
    estado: str | None = None,
    piso: str | None = None,
    tipo: str | None = None,
) -> pd.DataFrame:
    """
    filtra espacios segun criterios combinados y ordena los resultados
    por disponibilidad y capacidad mas ajustada al pedido.
    """
    resultado = df.copy()

    # filtros obligatorios
    if capacidad_min > 0:
        resultado = resultado[resultado["capacidad"] >= capacidad_min]

    # filtros opcionales
    if proyector is not None:
        resultado = resultado[resultado["tieneProyector"] == proyector]
    if estado:
        resultado = resultado[resultado["estadoActual"] == estado]
    if piso:
        resultado = resultado[resultado["piso"] == piso]
    if tipo:
        resultado = resultado[resultado["tipoEspacio"] == tipo]

    # ordenamiento inteligente
    orden_estado = {"Disponible": 0, "Ocupado": 1, "En Mantenimiento": 2}
    resultado = resultado.copy()
    resultado["_orden_estado"] = resultado["estadoActual"].map(orden_estado).fillna(3)
    resultado["_ajuste_cap"] = (resultado["capacidad"] - capacidad_min).abs()

    resultado = resultado.sort_values(["_orden_estado", "_ajuste_cap"])
    resultado = resultado.drop(columns=["_orden_estado", "_ajuste_cap"])

    return resultado.reset_index(drop=True)


# ---------------------------------------------------------------------------
# estadisticas para el dashboard
# ---------------------------------------------------------------------------

def resumen_estadisticas(df: pd.DataFrame) -> dict:
    """
    devuelve metricas generales del dataset para el dashboard de inicio.
    """
    conteo_estado = df["estadoActual"].value_counts()
    conteo_tipo = df["tipoEspacio"].value_counts()
    conteo_piso = df["piso"].value_counts()

    return {
        "total": len(df),
        "disponibles": int(conteo_estado.get("Disponible", 0)),
        "ocupados": int(conteo_estado.get("Ocupado", 0)),
        "en_mantenimiento": int(conteo_estado.get("En Mantenimiento", 0)),
        "con_proyector": int(df["tieneProyector"].sum()),
        "capacidad_total": int(df["capacidad"].sum()),
        "por_tipo": conteo_tipo.to_dict(),
        "por_piso": conteo_piso.to_dict(),
    }


def obtener_opciones_filtro(df: pd.DataFrame) -> dict:
    """
    devuelve las opciones unicas de cada columna filtrable,
    util para construir selectboxes en la ui.
    """
    return {
        "pisos": sorted(df["piso"].unique().tolist()),
        "tipos": sorted(df["tipoEspacio"].unique().tolist()),
        "estados": sorted(df["estadoActual"].unique().tolist()),
        "responsables": sorted(df["responsable"].unique().tolist()),
        "catedras": sorted(
            set(
                cat.strip()
                for cats in df["catedrasAsignadas"]
                for cat in cats.split(",")
                if cat.strip() != "Sin asignar"
            )
        ),
    }
