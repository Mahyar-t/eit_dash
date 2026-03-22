import dash_bootstrap_components as dbc
from dash import html, register_page

register_page(__name__, path="/")

layout = html.Div(
    className="index-shell",
)
