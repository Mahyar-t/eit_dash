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
                html.Div(
                    [
                        html.A("Dashboard", href="/load", id="nav-link-load", className="nav-text-link", style={"background": "transparent", "border": "none"}),
                        html.A("About us", href="/about", id="nav-link-about", className="nav-text-link", style={"background": "transparent", "border": "none"}),
                        html.A("Contact us", href="/contact", id="nav-link-contact", className="nav-text-link", style={"background": "transparent", "border": "none"}),
                    ],
                    className="top-navbar__links",
                ),
            ],
            id="top-navbar",
            className="top-navbar",
        ),

        # ── Sidebar ─────────────────────────────────────────────────────────
        dbc.Offcanvas(
            html.Div([
                html.P("Advanced Electrical Impedance Tomography Dashboard for real-time analysis and data processing.", className="page-intro", style={"fontSize": "1rem"}),
                html.Hr(style={"borderColor": "rgba(0,0,0,0.1)", "margin": "1.5rem 0"}),
                html.A(
                    [html.I(className="fas fa-chart-line", style={"marginRight": "10px"}), "Dashboard"],
                    href="/load",
                    id="sidebar-dashboard-link",
                    className="sidebar-nav-link text-decoration-none w-100 mb-3 d-block",
                ),
                html.A(
                    [html.I(className="fas fa-info-circle", style={"marginRight": "10px"}), "About us"],
                    href="/about",
                    id="sidebar-about-link",
                    className="sidebar-nav-link text-decoration-none w-100 mb-3 d-block",
                ),
                html.A(
                    [html.I(className="fas fa-envelope", style={"marginRight": "10px"}), "Contact us"],
                    href="/contact",
                    id="sidebar-contact-link",
                    className="sidebar-nav-link text-decoration-none w-100 mb-4 d-block",
                ),
                # html.P("Loaded datasets and selections will appear across all modules as you progress through the tab steps.", className="page-intro", style={"fontSize": "1rem", "opacity": "0.8", "textAlign": "justify"})
            ]),
            id="main-sidebar",
            title="Welcome to EIT-ALIVE",
            is_open=False,
            placement="start",
            className="glass-panel",
            style={"width": "336px", "backgroundColor": "rgba(255, 255, 255, 0.2)", "backdropFilter": "blur(10px)", "WebkitBackdropFilter": "blur(10px)", "border": "1px solid rgba(126, 126, 126, 0.1)", "borderRadius": "0"},
            backdrop=False,
        ),

        html.Div(
            [
                # ── Main content (tabs + pages) ─────────────────────────────
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H1('EIT Dashboard', id='test-id', className='app-title'),
                                        html.P(
                                            'A local workflow for loading, preparing, and analyzing EIT data. \n Loaded datasets and selections will appear across all modules as you progress through the tab steps.',
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
            ],
            className='app-shell',
        ),
        html.Footer(
            [
                html.Img(src='/assets/logo.png', className='footer-logo'),
                html.Span("© 2026 ROTARC Research Group. All Rights Reserved."),
            ],
            id="app-footer",
            className="app-footer"
        ),
    ],
    className='app-root',
)


@callback(
    Output('dashboard-shell', 'style'),
    Input('url', 'pathname'),
)
def toggle_shell_visibility(pathname):
    if pathname in ['/', '/about', '/contact']:
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


@callback(
    [
        Output('nav-link-load', 'className'),
        Output('nav-link-about', 'className'),
        Output('nav-link-contact', 'className'),
        Output('sidebar-dashboard-link', 'className'),
        Output('sidebar-about-link', 'className'),
        Output('sidebar-contact-link', 'className'),
    ],
    Input('url', 'pathname'),
)
def update_nav_active_class(pathname):
    dashboard_active = pathname in ["/load", "/preprocessing", "/analyze"]
    about_active = pathname == "/about"
    contact_active = pathname == "/contact"

    n_cls = lambda active, base: f"{base} active" if active else base

    return (
        n_cls(dashboard_active, "nav-text-link"),
        n_cls(about_active, "nav-text-link"),
        n_cls(contact_active, "nav-text-link"),
        n_cls(dashboard_active, "sidebar-nav-link text-decoration-none w-100 mb-3 d-block"),
        n_cls(about_active, "sidebar-nav-link text-decoration-none w-100 mb-3 d-block"),
        n_cls(contact_active, "sidebar-nav-link text-decoration-none w-100 mb-4 d-block"),
    )


if __name__ == '__main__':
    app.run_server(debug=False)
