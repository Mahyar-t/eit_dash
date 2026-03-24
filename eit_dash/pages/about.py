import dash_bootstrap_components as dbc
from dash import html, register_page

register_page(__name__, path="/about")

layout = html.Div(
    [
        html.H1("About Us", className="app-title"),
    ],
    className="app-header",
    style={"padding": "4rem", "textAlign": "center", "marginTop": "0"}
)
