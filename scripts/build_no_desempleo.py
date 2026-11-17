"""Reproduce las tablas de no desempleo: python scripts/build_no_desempleo.py."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEYS = ["CURSO", "COD_RUCT", "TITULACION", "CENTRO"]
VALUE = "P_NO_DESEMPLEADOS"


def normalize(df):
    df = df.copy()
    for col in KEYS:
        df[col] = df[col].astype("string").str.normalize("NFC").str.strip()
    if df[KEYS].isna().any().any() or df[KEYS].eq("").any().any():
        raise ValueError("Claves vacías")
    if df.duplicated(KEYS).any():
        raise ValueError("Claves duplicadas; revisar antes de integrar")
    return df


def load_raw(root=ROOT):
    frames, inventory = [], []
    for path in sorted((root / "data/raw/NoDesempleo").glob("*.csv")):
        encoding = "utf-8-sig"
        try:
            df = pd.read_csv(path, sep=";", encoding=encoding, dtype="string")
        except UnicodeDecodeError:
            encoding = "latin-1"
            df = pd.read_csv(path, sep=";", encoding=encoding, dtype="string")
        df = normalize(df)
        original = df[VALUE].str.strip()
        df[VALUE] = pd.to_numeric(original.str.replace(",", ".", regex=False), errors="coerce")
        invalid = (original.notna() & df[VALUE].isna()) | (df[VALUE].notna() & ~df[VALUE].between(0, 100))
        if invalid.any():
            raise ValueError(f"{path.name}: porcentajes inválidos")
        inventory.append({"ARCHIVO": path.name, "CODIFICACION": encoding,
                          "CURSOS": ", ".join(sorted(df.CURSO.unique())), "FILAS": len(df),
                          "CON_DATO": int(df[VALUE].count())})
        df["ARCHIVO_NO_DESEMPLEO"] = path.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError("No se encuentran CSV en data/raw/NoDesempleo")
    return normalize(pd.concat(frames, ignore_index=True)).sort_values(KEYS).reset_index(drop=True), pd.DataFrame(inventory)


def summarize(df):
    annual = df.groupby("CURSO", as_index=False).agg(
        REGISTROS=(VALUE, "size"), CON_DATO=(VALUE, "count"), MEDIA=(VALUE, "mean"),
        MEDIANA=(VALUE, "median"), MINIMO=(VALUE, "min"), MAXIMO=(VALUE, "max"))
    annual["COBERTURA_PCT"] = 100 * annual.CON_DATO / annual.REGISTROS
    return annual


def integrate(df, root=ROOT):
    processed = root / "data/processed"
    base = normalize(pd.read_csv(processed / "upv_titulaciones_eda.csv", dtype={"COD_RUCT": "string"}))
    merged = base.merge(df, on=KEYS, how="outer", validate="one_to_one", indicator="ORIGEN_INTEGRACION")
    # Completar matrícula de las filas nuevas (incluido 2019-20) desde su tabla detallada.
    matricula = normalize(pd.read_csv(processed / "upv_matricula.csv", dtype={"COD_RUCT": "string"}))
    merged = merged.merge(matricula[KEYS + ["NUMERO_ALUMNOS_MATRICULADOS"]], on=KEYS,
                          how="left", validate="one_to_one", suffixes=("", "_FUENTE"))
    merged["NUMERO_ALUMNOS_MATRICULADOS"] = merged.NUMERO_ALUMNOS_MATRICULADOS.combine_first(merged.NUMERO_ALUMNOS_MATRICULADOS_FUENTE)
    merged = merged.drop(columns="NUMERO_ALUMNOS_MATRICULADOS_FUENTE")
    coverage = merged.groupby("CURSO", as_index=False).agg(
        TOTAL_REGISTROS=("COD_RUCT", "size"), CON_NO_DESEMPLEO=(VALUE, "count"))
    coverage["CON_NO_DESEMPLEO_PCT"] = 100 * coverage.CON_NO_DESEMPLEO / coverage.TOTAL_REGISTROS
    return merged.sort_values(KEYS).reset_index(drop=True), coverage


def build(root=ROOT):
    df, inventory = load_raw(root)
    integrated, coverage = integrate(df, root)
    tables = {"upv_no_desempleo.csv": df, "upv_no_desempleo_anual.csv": summarize(df),
              "upv_no_desempleo_fuentes.csv": inventory, "upv_titulaciones_integrado.csv": integrated,
              "cobertura_no_desempleo.csv": coverage}
    for name, table in tables.items():
        table.to_csv(root / "data/processed" / name, index=False, encoding="utf-8-sig")
    return tables


if __name__ == "__main__":
    for name, table in build().items():
        print(f"{name}: {len(table)} filas")
