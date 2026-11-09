"""Dashboard UPV Benchmark.

Ejecutar desde la raíz del repositorio:
    streamlit run app.py
Los CSV se leen desde data/processed/; no se requiere ejecutar notebooks.
"""
import pandas as pd
import streamlit as st
import plotly.express as px

from dashboard.charts import bar, line, coverage_heatmap
from dashboard.data_loader import DATA_DIR, FILES, course_order, load_table, numeric

st.set_page_config(page_title="UPV Benchmark Explorer", page_icon="🎓", layout="wide")

# Tipografía y espaciado básico sin depender de imágenes o archivos estáticos.
st.markdown("""
<style>
.block-container {padding-top: 1.7rem; max-width: 1450px;}
[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.19); border-radius: 12px; padding: 12px;}
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
    except (ValueError, pd.errors.ParserError, UnicodeError) as exc:
        st.error(f"No se puede utilizar {FILES[key]}: {exc}")
        return None
    if df is None:
        st.warning(f"No se encuentra `data/processed/{FILES[key]}`. Añádelo al repositorio para activar esta sección.")
    return df


def plot(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})


def download_csv(df, name):
    st.download_button("Descargar datos filtrados (CSV)",
                       df.to_csv(index=False).encode("utf-8-sig"),
                       file_name=name, mime="text/csv")


st.sidebar.title("UPV Benchmark")
page = st.sidebar.radio(
    "Explorar", ["Resumen UPV", "Internacionalización", "Recursos académicos",
                "Presupuesto", "Calidad de datos"]
)
st.sidebar.divider()
st.sidebar.caption("Fuente: CSV procesados del repositorio GPR_university_benchmark.")
st.sidebar.caption("Las series tienen períodos de cobertura distintos.")

st.title("UPV Benchmark Explorer")
st.caption("Exploración interactiva de matrícula, movilidad internacional, PDI y recursos económicos")

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
        st.caption("Las titulaciones son códigos distintos; una titulación impartida en varios centros puede aparecer en varias filas del dato detallado.")
    if pdi is not None and not pdi.empty:
        pdi = numeric(pdi, ["PDI_TOTAL"])
        st.subheader("Personal docente e investigador")
        plot(line(pdi.sort_values("AÑO"), "AÑO", "PDI_TOTAL", "Evolución del PDI", "Personal PDI"))
    if ratio is not None and not ratio.empty:
        ratio = numeric(ratio, ["MATRICULAS_POR_PDI"])
        plot(line(ratio.sort_values("AÑO"), "AÑO", "MATRICULAS_POR_PDI", "Matrículas por PDI", "Matrículas / PDI"))
        st.caption("La ratio relaciona el año natural del PDI con el curso académico que comienza ese año.")

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
        b.metric("Movilidad entrante / matrícula*", fmt_pct(weighted_ratio))
        c.metric("Media % movilidad saliente**", fmt_pct(outgoing_valid.mean()))
        e.metric("Con datos para ratio", f"{len(valid)}/{len(d)}")
        st.caption("* Ratio agregada calculada solo con filas con movilidad y matrícula válidas; no representa necesariamente toda la UPV. ** Media simple de porcentajes de titulaciones-centro disponibles; no es una tasa global de alumnos salientes.")
        if d.empty:
            st.info("No hay registros con esos filtros.")
        else:
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
            st.markdown("#### Explorar titulaciones")
            view = d.copy()
            view["RATIO_MOVILIDAD_ENTRANTE"] = pd.NA
            good = view["MOVILIDAD_ENTRANTE"].notna() & view["NUMERO_ALUMNOS_MATRICULADOS"].notna() & (view["NUMERO_ALUMNOS_MATRICULADOS"] > 0)
            view.loc[good, "RATIO_MOVILIDAD_ENTRANTE"] = 100 * view.loc[good, "MOVILIDAD_ENTRANTE"] / view.loc[good, "NUMERO_ALUMNOS_MATRICULADOS"]
            view["RATIO_MOVILIDAD_ENTRANTE"] = pd.to_numeric(view["RATIO_MOVILIDAD_ENTRANTE"], errors="coerce")
            cols = ["CURSO", "COD_RUCT", "TITULACION", "CENTRO", "MOVILIDAD_ENTRANTE", "PORC_MOVILIDAD_SALIENTE", "NUMERO_ALUMNOS_MATRICULADOS", "RATIO_MOVILIDAD_ENTRANTE"]
            st.dataframe(view[cols].sort_values("MOVILIDAD_ENTRANTE", ascending=False), use_container_width=True, hide_index=True)
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
        st.caption("PDI representado como suma de la columna CASOS, no como recuento de filas.")
        left, right = st.columns(2)
        with left:
            categories = d.groupby("CATEGORÍA", as_index=False)["CASOS"].sum().sort_values("CASOS", ascending=False).head(12)
            if not categories.empty:
                plot(bar(categories.sort_values("CASOS"), "CASOS", "CATEGORÍA", "PDI por categoría", "Personas", "", "h"))
        with right:
            sexes = d.groupby("SEXO", as_index=False)["CASOS"].sum()
            if not sexes.empty:
                fig = px.pie(sexes, values="CASOS", names="SEXO", title="Distribución por sexo", hole=.45)
                plot(fig)
        departments = d.groupby("DEPARTAMENTO", as_index=False)["CASOS"].sum().sort_values("CASOS", ascending=False).head(15)
        if not departments.empty:
            plot(bar(departments.sort_values("CASOS"), "CASOS", "DEPARTAMENTO", "Departamentos con más PDI", "Personas", "", "h"))
        with st.expander("Ver registros detallados"):
            st.dataframe(d, use_container_width=True, hide_index=True)
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
        st.caption("Gasto ejecutado: obligaciones reconocidas netas. No equivale necesariamente a pagos realizados.")
        if detail is not None:
            detail = numeric(detail, ["OBLIGACIONES_RECONOCIDAS_NETAS_EUR", "PRESUPUESTO_DEFINITIVO_EUR"])
            d = detail[detail["AÑO"] == year]
            chapters = d.groupby("DESCRIPCION_CAPITULO", as_index=False)["OBLIGACIONES_RECONOCIDAS_NETAS_EUR"].sum().sort_values("OBLIGACIONES_RECONOCIDAS_NETAS_EUR")
            if not chapters.empty:
                plot(bar(chapters, "OBLIGACIONES_RECONOCIDAS_NETAS_EUR", "DESCRIPCION_CAPITULO", "Gasto por capítulo", "Euros", "", "h"))
        if per_student is not None:
            per_student = numeric(per_student, ["GASTO_POR_MATRICULA"])
            plot(line(per_student.sort_values("AÑO"), "AÑO", "GASTO_POR_MATRICULA", "Gasto ejecutado por matrícula", "Euros / matrícula"))
            st.caption("Cálculo con matrícula del curso que comienza en el mismo año natural del presupuesto. Es una aproximación metodológica.")

elif page == "Calidad de datos":
    st.subheader("Cobertura y disponibilidad")
    cov = get("cobertura")
    full = get("cobertura_completa")
    if cov is not None and not cov.empty:
        cols = ["CON_MATRICULA_PCT", "CON_MOVILIDAD_ENTRANTE_PCT", "CON_MOVILIDAD_SALIENTE_PCT"]
        cov = numeric(cov, cols + ["TOTAL_REGISTROS"])
        cov["CURSO"] = pd.Categorical(cov["CURSO"], categories=course_order(cov["CURSO"]), ordered=True)
        cov = cov.sort_values("CURSO")
        plot(coverage_heatmap(cov))
        st.dataframe(cov, use_container_width=True, hide_index=True)
        download_csv(cov, "upv_cobertura_por_curso.csv")
    if full is not None and not full.empty:
        full = numeric(full, ["COMPLETOS", "TOTAL", "COBERTURA_COMPLETA_PCT"])
        full = full.sort_values("CURSO")
        plot(bar(full, "CURSO", "COBERTURA_COMPLETA_PCT", "Cobertura simultánea de matrícula, movilidad entrante y saliente", "", "Cobertura (%)"))
        st.dataframe(full, use_container_width=True, hide_index=True)
    st.info("Estos porcentajes miden la disponibilidad entre las filas del dataset integrado de movilidad (159 por curso en la versión actual), no la cobertura de toda la oferta de titulaciones de la UPV. Un valor ausente no significa cero estudiantes.")

st.divider()
st.caption("Proyecto GPR · UPV · Datos públicos procesados con pandas. Revisar los indicadores y su cobertura antes de compararlos entre períodos o centros.")
