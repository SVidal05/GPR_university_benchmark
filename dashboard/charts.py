"""Funciones Plotly reutilizables del dashboard."""
import plotly.express as px
import plotly.graph_objects as go

PALETTE = ["#277DA1", "#43AA8B", "#F9C74F", "#F3722C", "#577590"]


def line(df, x, y, title, y_label, color=None):
    fig = px.line(
        df, x=x, y=y, color=color, markers=True,
        title=title, color_discrete_sequence=PALETTE,
    )
    fig.update_layout(xaxis_title="", yaxis_title=y_label, legend_title_text="",
                      margin=dict(l=10, r=10, t=55, b=15), hovermode="x unified")
    return fig


def bar(df, x, y, title, x_label="", y_label="", orientation="v", color=None):
    fig = px.bar(
        df, x=x, y=y, orientation=orientation, color=color,
        title=title, color_discrete_sequence=PALETTE,
    )
    fig.update_layout(xaxis_title=x_label, yaxis_title=y_label,
                      legend_title_text="", margin=dict(l=10, r=10, t=55, b=15))
    return fig


def coverage_heatmap(df):
    z = df[["CON_MATRICULA_PCT", "CON_MOVILIDAD_ENTRANTE_PCT", "CON_MOVILIDAD_SALIENTE_PCT"]].T
    fig = go.Figure(go.Heatmap(
        z=z.values, x=df["CURSO"].astype(str).tolist(),
        y=["Matrícula", "Movilidad entrante", "Movilidad saliente"],
        zmin=0, zmax=100, colorscale="YlGn", zsmooth=False,
        text=[[f"{v:.1f}%" for v in row] for row in z.values], texttemplate="%{text}",
        hovertemplate="%{y} · %{x}: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="%"),
    ))
    fig.update_layout(title="Cobertura por curso en la tabla integrada",
                      xaxis_title="Curso académico", margin=dict(l=10, r=10, t=55, b=15))
    return fig
