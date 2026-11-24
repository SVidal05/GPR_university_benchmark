"""Funciones Plotly reutilizables del dashboard."""
import plotly.express as px
PALETTE = ["#547539", "#8ea85f", "#b4bb7a", "#517b73", "#a8814e"]


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
