"""Dashboard UPV Benchmark.

Ejecutar desde la raíz del repositorio:
    streamlit run app.py
Los CSV se leen desde data/processed/; no se requiere ejecutar notebooks.
"""
import logging

import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard.charts import PALETTE, bar, line
from dashboard.data_loader import FILES, course_order, load_table, numeric

logger = logging.getLogger(__name__)

st.set_page_config(page_title="UPV Benchmark Explorer", page_icon="🎓", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 3.5rem; max-width: 1380px;}
.st-key-section_navigation [aria-label="Secciones"] {
    gap: .55rem;
    padding: .25rem .2rem .7rem;
    border-bottom: 1px solid #aab991;
}
.st-key-section_navigation button[data-variant="segmented_control"] {
    min-height: 2.75rem;
    padding: .55rem 1rem;
    border: 1px solid #aab991;
    border-radius: .4rem;
    background: #eef2e5;
    color: #344420;
    transition: background-color .15s ease;
}
.st-key-section_navigation button[data-variant="segmented_control"] p {
    font-weight: 600;
}
.st-key-section_navigation button[data-variant="segmented_control"]:hover {
    background: #dbe5ca;
}
.st-key-section_navigation button[data-variant="segmented_control"][data-selected] {
    background: #b6cb93;
    border-color: #718a4e;
    box-shadow: inset 0 -3px #718a4e;
}
.st-key-section_navigation button[data-variant="segmented_control"]:focus-visible {
    outline: 2px solid #536b37;
    outline-offset: 2px;
}
[data-testid="stMetric"] {
    background: #f0f4e7;
    color: #344420;
    border: 1px solid #d6dfc2;
    border-top: 3px solid #a4b883;
    border-radius: .7rem;
    padding: .8rem 1rem;
}
[data-testid="stMetric"] p {color: #344420;}
</style>
""", unsafe_allow_html=True)


def fmt_int(value):
    return "—" if pd.isna(value) else f"{value:,.0f}".replace(",", ".")


def fmt_pct(value):
    return "—" if pd.isna(value) else f"{value:.1f}%".replace(".", ",")


def fmt_eur(value):
    return "—" if pd.isna(value) else f"{value:,.0f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def get(key):
    try:
        df = load_table(key)
    except (ValueError, pd.errors.ParserError, UnicodeError):
        logger.exception("No se puede utilizar %s", FILES[key])
        return None
    if df is None:
        logger.warning("No se encuentra data/processed/%s", FILES[key])
    return df


def plot(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def download_csv(df, name):
    st.download_button("Descargar datos filtrados (CSV)",
                       df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=name, mime="text/csv")


st.title("UPV Benchmark Explorer")
page = st.segmented_control(
    "Secciones", ["Resumen UPV", "Internacionalización", "Recursos académicos",
                  "Presupuesto", "No desempleo", "Calidad de datos"],
    default="Resumen UPV",
    required=True,
    wrap=True,
    key="section_navigation",
    label_visibility="collapsed",
)

if page == "Resumen UPV":
    st.subheader("Evolución institucional")
    matricula = get("matricula_anual")
    pdi = get("pdi_anual")
    ratio = get("pdi_matricula")
    if matricula is not None and not matricula.empty:
        matricula = numeric(matricula, ["ALUMNOS", "TITULACIONES", "CENTROS"])
        matricula["CURSO"] = pd.Categorical(matricula["CURSO"], categories=course_order(matricula["CURSO"]), ordered=True)
        matricula = matricula.sort_values("CURSO")
        ultimo = matricula.iloc[-1]
        a, b, c = st.columns(3)
        a.metric(f"Matrículas · {ultimo['CURSO']}", fmt_int(ultimo["ALUMNOS"]))
        b.metric("Titulaciones (códigos únicos)", fmt_int(ultimo["TITULACIONES"]))
        c.metric("Centros", fmt_int(ultimo["CENTROS"]))
        plot(line(matricula, "CURSO", "ALUMNOS", "Evolución de matrículas", "Alumnos matriculados"))
        plot(line(matricula, "CURSO", "TITULACIONES", "Evolución de titulaciones", "Códigos de titulación diferentes"))
    if pdi is not None and not pdi.empty:
        pdi = numeric(pdi, ["PDI_TOTAL"])
        st.subheader("Personal docente e investigador")
        plot(line(pdi.sort_values("AÑO"), "AÑO", "PDI_TOTAL", "Evolución del PDI", "Personal PDI"))
    if ratio is not None and not ratio.empty:
        ratio = numeric(ratio, ["MATRICULAS_POR_PDI"])
        plot(line(ratio.sort_values("AÑO"), "AÑO", "MATRICULAS_POR_PDI", "Matrículas por PDI", "Matrículas / PDI"))

elif page == "Internacionalización":
    st.subheader("Movilidad por titulación y centro")
    df = get("movilidad")
    if df is not None and not df.empty:
        df = numeric(df, ["MOVILIDAD_ENTRANTE", "PORC_MOVILIDAD_SALIENTE", "NUMERO_ALUMNOS_MATRICULADOS"])
        cursos = course_order(df["CURSO"])
        curso = st.selectbox("Curso académico", cursos, index=len(cursos)-1)
        d = df.loc[df["CURSO"] == curso].copy()
        centros = sorted(d["CENTRO"].dropna().astype(str).unique())
        selected_centros = st.multiselect("Centros (vacío = todos)", centros)
        if selected_centros:
            d = d[d["CENTRO"].isin(selected_centros)]
        titulaciones = sorted(d["TITULACION"].dropna().astype(str).unique())
        selected_titles = st.multiselect("Titulaciones (vacío = todas)", titulaciones)
        if selected_titles:
            d = d[d["TITULACION"].isin(selected_titles)]
        valid = d.loc[
            d["MOVILIDAD_ENTRANTE"].notna()
            & d["NUMERO_ALUMNOS_MATRICULADOS"].notna()
            & (d["NUMERO_ALUMNOS_MATRICULADOS"] > 0)
        ].copy()
        incoming_total = d["MOVILIDAD_ENTRANTE"].sum(min_count=1)
        outgoing_valid = d["PORC_MOVILIDAD_SALIENTE"].dropna()
        weighted_ratio = (100 * valid["MOVILIDAD_ENTRANTE"].sum() /
                          valid["NUMERO_ALUMNOS_MATRICULADOS"].sum()) if len(valid) else float("nan")
        a, b, c, e = st.columns(4)
        a.metric("Movilidad entrante registrada", fmt_int(incoming_total))
        b.metric("Entrantes / matrícula en filas completas", fmt_pct(weighted_ratio))
        c.metric("Media de movilidad saliente", fmt_pct(outgoing_valid.mean()))
        e.metric("Con datos para ratio", f"{len(valid)}/{len(d)}")
        if not d.empty:
            left, right = st.columns(2)
            with left:
                incoming = d.dropna(subset=["MOVILIDAD_ENTRANTE"]).groupby("CENTRO", as_index=False)["MOVILIDAD_ENTRANTE"].sum().sort_values("MOVILIDAD_ENTRANTE", ascending=False).head(15)
                if not incoming.empty:
                    plot(bar(incoming.sort_values("MOVILIDAD_ENTRANTE"), "MOVILIDAD_ENTRANTE", "CENTRO", "Estudiantes recibidos por centro (registros disponibles)", "Estudiantes", "", "h"))
            with right:
                if not valid.empty:
                    by_center = valid.groupby("CENTRO", as_index=False).agg(entrantes=("MOVILIDAD_ENTRANTE", "sum"), matriculas=("NUMERO_ALUMNOS_MATRICULADOS", "sum"))
                    by_center["RATIO"] = 100 * by_center["entrantes"] / by_center["matriculas"]
                    by_center = by_center.sort_values("RATIO").tail(15)
                    plot(bar(by_center, "RATIO", "CENTRO", "Movilidad por 100 matriculados (filas completas)", "Porcentaje (%)", "", "h"))
            view = d.copy()
            view["RATIO_MOVILIDAD_ENTRANTE"] = pd.NA
            good = view["MOVILIDAD_ENTRANTE"].notna() & view["NUMERO_ALUMNOS_MATRICULADOS"].notna() & (view["NUMERO_ALUMNOS_MATRICULADOS"] > 0)
            view.loc[good, "RATIO_MOVILIDAD_ENTRANTE"] = 100 * view.loc[good, "MOVILIDAD_ENTRANTE"] / view.loc[good, "NUMERO_ALUMNOS_MATRICULADOS"]
            view["RATIO_MOVILIDAD_ENTRANTE"] = pd.to_numeric(view["RATIO_MOVILIDAD_ENTRANTE"], errors="coerce")
            cols = ["CURSO", "COD_RUCT", "TITULACION", "CENTRO", "MOVILIDAD_ENTRANTE", "PORC_MOVILIDAD_SALIENTE", "NUMERO_ALUMNOS_MATRICULADOS", "RATIO_MOVILIDAD_ENTRANTE"]
            download_csv(view[cols], f"upv_movilidad_{curso}.csv")

elif page == "Recursos académicos":
    st.subheader("Personal docente e investigador")
    df = get("pdi")
    if df is not None and not df.empty:
        df = numeric(df, ["CASOS"])
        years = sorted(df["AÑO"].dropna().unique().astype(int).tolist())
        year = st.selectbox("Año", years, index=len(years)-1)
        d = df[df["AÑO"] == year].copy()
        colectivos = sorted(d["COLECTIVO"].dropna().astype(str).unique())
        chosen = st.multiselect("Colectivo (vacío = todos)", colectivos)
        if chosen:
            d = d[d["COLECTIVO"].isin(chosen)]
        st.metric("PDI registrado en la selección", fmt_int(d["CASOS"].sum()))
        left, right = st.columns(2)
        with left:
            categories = d.groupby("CATEGORÍA", as_index=False)["CASOS"].sum().sort_values("CASOS", ascending=False).head(12)
            if not categories.empty:
                plot(bar(categories.sort_values("CASOS"), "CASOS", "CATEGORÍA", "PDI por categoría", "Personas", "", "h"))
        with right:
            sexes = d.groupby("SEXO", as_index=False)["CASOS"].sum()
            if not sexes.empty:
                fig = px.pie(sexes, values="CASOS", names="SEXO", color_discrete_sequence=PALETTE, title="Distribución por sexo", hole=.45)
                plot(fig)
        departments = d.groupby("DEPARTAMENTO", as_index=False)["CASOS"].sum().sort_values("CASOS", ascending=False).head(15)
        if not departments.empty:
            plot(bar(departments.sort_values("CASOS"), "CASOS", "DEPARTAMENTO", "Departamentos con más PDI", "Personas", "", "h"))
        download_csv(d, f"upv_pdi_{year}.csv")

elif page == "Presupuesto":
    st.subheader("Presupuesto y ejecución del gasto")
    annual = get("presupuesto_anual")
    detail = get("presupuesto")
    per_student = get("presupuesto_matricula")
    if annual is not None and not annual.empty:
        annual = numeric(annual, ["PRESUPUESTO_DEFINITIVO", "GASTO_EJECUTADO", "EJECUCION_PCT"])
        annual = annual.sort_values("AÑO")
        years = annual["AÑO"].dropna().astype(int).tolist()
        year = st.selectbox("Año presupuestario", years, index=len(years)-1)
        cur = annual.loc[annual["AÑO"] == year].iloc[0]
        a, b, c = st.columns(3)
        a.metric("Presupuesto definitivo", fmt_eur(cur["PRESUPUESTO_DEFINITIVO"]))
        b.metric("Gasto ejecutado", fmt_eur(cur["GASTO_EJECUTADO"]))
        c.metric("Ejecución presupuestaria", fmt_pct(cur["EJECUCION_PCT"]))
        series = annual.melt(id_vars="AÑO", value_vars=["PRESUPUESTO_DEFINITIVO", "GASTO_EJECUTADO"], var_name="Indicador", value_name="Euros")
        plot(line(series, "AÑO", "Euros", "Evolución de presupuesto y gasto", "Euros", color="Indicador"))
        if detail is not None:
            detail = numeric(detail, ["OBLIGACIONES_RECONOCIDAS_NETAS_EUR", "PRESUPUESTO_DEFINITIVO_EUR"])
            d = detail[detail["AÑO"] == year]
            chapters = d.groupby("DESCRIPCION_CAPITULO", as_index=False)["OBLIGACIONES_RECONOCIDAS_NETAS_EUR"].sum().sort_values("OBLIGACIONES_RECONOCIDAS_NETAS_EUR")
            if not chapters.empty:
                plot(bar(chapters, "OBLIGACIONES_RECONOCIDAS_NETAS_EUR", "DESCRIPCION_CAPITULO", "Gasto por capítulo", "Euros", "", "h"))
        if per_student is not None:
            per_student = numeric(per_student, ["GASTO_POR_MATRICULA"])
            plot(line(per_student.sort_values("AÑO"), "AÑO", "GASTO_POR_MATRICULA", "Gasto ejecutado por matrícula", "Euros / matrícula"))

elif page == "No desempleo":
    st.subheader("Porcentaje de no desempleados por titulación y centro")
    df = get("no_desempleo")
    if df is not None and not df.empty:
        df = numeric(df, ["P_NO_DESEMPLEADOS"])
        # Solo filas presentes en la fuente, incluso si en futuras entregas tienen nulos.
        df = df[df["ARCHIVO_NO_DESEMPLEO"].notna()].copy()
        centros = sorted(df["CENTRO"].dropna().unique())
        selected_centros = st.multiselect("Centros (vacío = todos)", centros)
        if selected_centros:
            df = df[df["CENTRO"].isin(selected_centros)]
        titles = sorted(df["TITULACION"].dropna().unique())
        selected_titles = st.multiselect("Titulaciones (vacío = todas)", titles)
        if selected_titles:
            df = df[df["TITULACION"].isin(selected_titles)]
        cursos = course_order(df["CURSO"])
        if cursos:
            curso = st.selectbox("Curso académico", cursos, index=len(cursos)-1)
            d = df[df["CURSO"] == curso].copy()
            a, b, c = st.columns(3)
            a.metric("Media simple", fmt_pct(d["P_NO_DESEMPLEADOS"].mean()))
            b.metric("Mediana", fmt_pct(d["P_NO_DESEMPLEADOS"].median()))
            c.metric("Registros con dato / publicados", f"{d['P_NO_DESEMPLEADOS'].count()} / {len(d)}")
            annual = df.groupby("CURSO", as_index=False).agg(MEDIA=("P_NO_DESEMPLEADOS", "mean"), MEDIANA=("P_NO_DESEMPLEADOS", "median"))
            series = annual.melt(id_vars="CURSO", var_name="Estadístico", value_name="Porcentaje")
            fig = line(series, "CURSO", "Porcentaje", "Evolución entre registros disponibles", "Porcentaje (%)", color="Estadístico")
            fig.update_yaxes(range=[0, 100])
            plot(fig)
            valid = d.dropna(subset=["P_NO_DESEMPLEADOS"])
            if not valid.empty:
                left, right = st.columns(2)
                with left:
                    centers = valid.groupby("CENTRO", as_index=False).agg(MEDIA=("P_NO_DESEMPLEADOS", "mean"), REGISTROS=("P_NO_DESEMPLEADOS", "count"))
                    fig = px.bar(centers.sort_values("MEDIA"), x="MEDIA", y="CENTRO", orientation="h", hover_data=["REGISTROS"], color_discrete_sequence=PALETTE, title="Media simple por centro")
                    fig.update_xaxes(title="Porcentaje (%)", range=[0, 100])
                    plot(fig)
                with right:
                    fig = px.histogram(valid, x="P_NO_DESEMPLEADOS", nbins=20, color_discrete_sequence=PALETTE, title="Distribución entre titulaciones-centro")
                    fig.update_xaxes(title="Porcentaje (%)", range=[0, 100])
                    fig.update_yaxes(title="Registros")
                    plot(fig)
            columns = ["CURSO", "COD_RUCT", "TITULACION", "CENTRO", "P_NO_DESEMPLEADOS", "ARCHIVO_NO_DESEMPLEO"]
            download_csv(d[columns], f"upv_no_desempleo_{curso}.csv")

elif page == "Calidad de datos":
    st.subheader("Cobertura y disponibilidad")
    employment_coverage = get("cobertura_no_desempleo")
    if employment_coverage is not None and not employment_coverage.empty:
        plot(bar(employment_coverage, "CURSO", "CON_NO_DESEMPLEO_PCT", "Cobertura de no desempleo en el dataset integrado", "Curso", "Cobertura (%)"))
    cov = get("cobertura")
    full = get("cobertura_completa")
    if cov is not None and not cov.empty:
        indicators = {
            "CON_MATRICULA_PCT": "Matrícula",
            "CON_MOVILIDAD_ENTRANTE_PCT": "Movilidad entrante",
            "CON_MOVILIDAD_SALIENTE_PCT": "Movilidad saliente",
        }
        cov = numeric(cov, list(indicators) + ["TOTAL_REGISTROS"])
        cov["CURSO"] = pd.Categorical(cov["CURSO"], categories=course_order(cov["CURSO"]), ordered=True)
        cov = cov.sort_values("CURSO")
        series = cov.rename(columns=indicators).melt(
            id_vars="CURSO", value_vars=list(indicators.values()),
            var_name="Indicador", value_name="Cobertura",
        ).sort_values("CURSO")
        fig = bar(series, "CURSO", "Cobertura", "Cobertura por curso",
                  "Curso académico", "Cobertura (%)", color="Indicador")
        fig.update_layout(barmode="group")
        fig.update_yaxes(range=[0, 100])
        plot(fig)
        download_csv(cov, "upv_cobertura_por_curso.csv")
    if full is not None and not full.empty:
        full = numeric(full, ["COMPLETOS", "TOTAL", "COBERTURA_COMPLETA_PCT"])
        full = full.sort_values("CURSO")
        plot(bar(full, "CURSO", "COBERTURA_COMPLETA_PCT", "Cobertura simultánea de matrícula, movilidad entrante y saliente", "", "Cobertura (%)"))
