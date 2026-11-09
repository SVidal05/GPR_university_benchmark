"""Carga y validación de las tablas procesadas del proyecto UPV."""
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

FILES = {
    "matricula": "upv_matricula.csv",
    "matricula_anual": "upv_matricula_anual.csv",
    "pdi": "upv_pdi.csv",
    "pdi_anual": "upv_pdi_anual.csv",
    "pdi_matricula": "upv_pdi_matricula.csv",
    "presupuesto": "upv_presupuesto.csv",
    "presupuesto_anual": "upv_presupuesto_anual.csv",
    "presupuesto_matricula": "upv_presupuesto_matricula.csv",
    "movilidad": "upv_titulaciones_eda.csv",
    "cobertura": "cobertura_por_curso.csv",
    "cobertura_completa": "cobertura_completa.csv",
}

REQUIRED_COLUMNS = {
    "matricula": {"CURSO", "COD_RUCT", "TITULACION", "CENTRO", "NUMERO_ALUMNOS_MATRICULADOS"},
    "matricula_anual": {"CURSO", "ALUMNOS", "TITULACIONES", "CENTROS"},
    "pdi": {"AÑO", "COLECTIVO", "DEPARTAMENTO", "CATEGORÍA", "SEXO", "CASOS"},
    "pdi_anual": {"AÑO", "PDI_TOTAL"},
    "pdi_matricula": {"AÑO", "PDI_TOTAL", "MATRICULAS_POR_PDI"},
    "presupuesto": {"AÑO", "CAPITULO", "DESCRIPCION_CAPITULO", "PRESUPUESTO_DEFINITIVO_EUR", "OBLIGACIONES_RECONOCIDAS_NETAS_EUR"},
    "presupuesto_anual": {"AÑO", "PRESUPUESTO_DEFINITIVO", "GASTO_EJECUTADO", "EJECUCION_PCT"},
    "presupuesto_matricula": {"AÑO", "GASTO_POR_MATRICULA"},
    "movilidad": {"COD_RUCT", "TITULACION", "CENTRO", "CURSO", "MOVILIDAD_ENTRANTE", "PORC_MOVILIDAD_SALIENTE", "NUMERO_ALUMNOS_MATRICULADOS"},
    "cobertura": {"CURSO", "TOTAL_REGISTROS", "CON_MATRICULA_PCT", "CON_MOVILIDAD_ENTRANTE_PCT", "CON_MOVILIDAD_SALIENTE_PCT"},
    "cobertura_completa": {"CURSO", "TOTAL", "COMPLETOS", "COBERTURA_COMPLETA_PCT"},
}

@st.cache_data(show_spinner=False)
def load_table(key: str) -> pd.DataFrame | None:
    """Carga un CSV desde el proyecto, sin consultar internet ni ejecutar notebooks."""
    path = DATA_DIR / FILES[key]
    if not path.is_file():
        return None
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    missing = REQUIRED_COLUMNS[key] - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: faltan columnas {', '.join(sorted(missing))}")
    if "CURSO" in df.columns:
        df["CURSO"] = df["CURSO"].astype("string").str.strip()
    if "AÑO" in df.columns:
        df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
    return df


def course_order(values) -> list[str]:
    """Ordena cursos de tipo '2020-21' por año inicial."""
    xs = [str(v) for v in values if pd.notna(v)]
    return sorted(set(xs), key=lambda v: (int(v[:4]) if v[:4].isdigit() else 9999, v))


def numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convierte variables cuantitativas de CSV ya procesados."""
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df
