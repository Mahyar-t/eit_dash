import dash_bootstrap_components as dbc
from dash import html, register_page

register_page(__name__, path="/contact")

layout = html.Div(
    [
        html.H1("Contact Us", className="app-title"),
    ],
    className="app-header",
    style={"padding": "4rem", "textAlign": "center", "marginTop": "0"}
)
