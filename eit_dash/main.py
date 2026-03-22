import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, page_container, callback, State

from eit_dash.app import app
from eit_dash.callbacks import (  # noqa: F401
    analyze_callbacks,
    load_callbacks,
    preprocessing_callbacks,
)
from eit_dash.definitions import layout_styles as styles


process_stepper = html.Div(
    [
        dbc.NavLink(
            [
                html.Span('Step 1 - Load', className='process-tab-label'),
            ],
            href='/load',
            active='exact',
            className='process-tab',
            style=styles.PAGES_LINK,
        ),
        dbc.NavLink(
            [
                html.Span('Step 2 - Pre-process', className='process-tab-label'),
            ],
            href='/preprocessing',
            active='exact',
            className='process-tab',
            style=styles.PAGES_LINK,
        ),
        dbc.NavLink(
            [
                html.Span('Step 3 - Analyze', className='process-tab-label'),
            ],
            href='/analyze',
            active='exact',
            className='process-tab',
            style=styles.PAGES_LINK,
        ),
    ],
    className='process-stepper',
)

app.layout = html.Div(
    [
        dcc.Location(id='url', refresh=False),

        # ── Full-width glass top navbar ─────────────────────────────────────
        html.Nav(
            [
                dbc.Button(
                    html.I(className="fas fa-bars"),
                    id="open-sidebar-btn",
                    className="p-0 border-0 bg-transparent",
                    style={"fontSize": "1.2rem", "color": "var(--ink)", "boxShadow": "none", "opacity": "0.75"},
                ),
                html.A(
                    [
                        html.Img(src='/assets/logo_up.png', className='app-logo-img'),
                        html.Span('EIT-ALIVE'),
                    ],
                    href='/',
                    className='app-logo-text',
                    style={"position": "static", "margin": "0"}
                ),
            ],
            className="top-navbar",
        ),

        # ── Sidebar ─────────────────────────────────────────────────────────
        dbc.Offcanvas(
            html.Div([
                html.P("Advanced Electrical Impedance Tomography Dashboard for real-time analysis and data processing.", className="page-intro", style={"fontSize": "1.1rem"}),
                html.Hr(style={"borderColor": "rgba(0,0,0,0.1)", "margin": "1.5rem 0"}),
                dbc.Button(
                    [html.I(className="fas fa-chart-line", style={"marginRight": "10px"}), "Dashboard"],
                    href="/load",
                    id="sidebar-dashboard-link",
                    className="glass-button glass-button--primary w-100 mb-4",
                    style={"textAlign": "left", "padding": "12px 20px", "fontSize": "1.1rem"}
                ),
                html.P("Loaded datasets and selections will appear across all modules as you progress through the tab steps.", className="page-intro", style={"fontSize": "0.95rem", "opacity": "0.8"})
            ]),
            id="main-sidebar",
            title="Welcome to EIT-ALIVE",
            is_open=False,
            placement="start",
            className="glass-panel",
            style={"width": "280px", "backgroundColor": "rgba(255, 255, 255, 0.45)", "backdropFilter": "blur(28px)", "borderRight": "1px solid var(--card-border)", "borderRadius": "0"}
        ),

        # ── Main content (tabs + pages) ─────────────────────────────────────
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H1('EIT Dashboard', id='test-id', className='app-title'),
                                html.P(
                                    'A cleaner local workflow for loading, preparing, and analyzing EIT data.',
                                    className='app-subtitle',
                                ),
                            ],
                            className='app-brand',
                        ),
                    ],
                    className='app-header',
                ),
                process_stepper,
            ],
            id='dashboard-shell',
        ),
        html.Div(page_container, className='app-page-wrapper'),
        html.Footer(
            [
                html.Img(src='/assets/logo.png', className='footer-logo'),
                html.Span("© 2026 ROTARC Research Group. All Rights Reserved."),
            ],
            className="app-footer"
        ),
    ],
    className='app-shell',
)


@callback(
    Output('dashboard-shell', 'style'),
    Input('url', 'pathname'),
)
def toggle_shell_visibility(pathname):
    if pathname == '/':
        return {'display': 'none'}
    return {'display': 'block'}


@callback(
    Output("main-sidebar", "is_open"),
    Input("open-sidebar-btn", "n_clicks"),
    Input("sidebar-dashboard-link", "n_clicks"),
    State("main-sidebar", "is_open"),
    prevent_initial_call=True
)
def toggle_sidebar(n1, n2, is_open):
    return not is_open


if __name__ == '__main__':
    app.run_server(debug=False)
