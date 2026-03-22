import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

import eit_dash.definitions.element_ids as ids
import eit_dash.definitions.layout_styles as styles

register_page(__name__, path="/analyze")

summary = html.Div(
    [
        html.H2("Summary", style=styles.COLUMN_TITLE),
        html.Div([], id=ids.SUMMARY_COLUMN_ANALYZE, style=styles.LOAD_RESULTS),
    ],
    className="workflow-section workflow-section--feature workflow-section--summary",
)

results = html.Div(
    [
        html.H2("Results", id=ids.ANALYZE_RESULTS_TITLE, style=styles.COLUMN_TITLE),
        html.Div(
            [
                html.Div(id=ids.DATASET_CONTAINER, style=styles.LOAD_RESULTS),
                html.Div(
                    [
                        dcc.Graph(id=ids.EELI_RESULTS_GRAPH, style=styles.EMPTY_ELEMENT),
                    ],
                    id=ids.EELI_RESULTS_GRAPH_DIV,
                    hidden=True,
                ),
            ],
            className="glass-panel--results",
        ),
    ],
    className="workflow-section workflow-section--feature workflow-section--results",
)

actions = html.Div(
    [
        html.H2("Analyze", id=ids.ANALYZE_TITLE, style=styles.COLUMN_TITLE),
        html.P(
            "Run the selected analysis step and review each period inside a cleaner results surface.",
            className="panel-copy",
        ),
        html.Div(
            [
                html.H6("Select a period to view the results"),
                dbc.Select(id=ids.ANALYZE_SELECT_PERIOD_VIEW, className="w-100", style={"minHeight": "52px", "borderRadius": "16px"}),
            ],
        ),
        html.Div(className="compact-spacer"),
        dbc.Button("Apply EELI", id=ids.EELI_APPLY, disabled=False, className="glass-button glass-button--primary w-100"),
    ],
    className="workflow-section workflow-section--feature",
)

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.P("Step 3 - Analyze Data", className="page-kicker"),
                        html.P(
                            "Review the saved periods, launch the analysis, and inspect the output without losing the sense of flow.",
                            className="page-intro",
                        ),
                    ],
                    className="page-hero",
                ),
                html.Div([summary, actions, results], className="workflow-board"),
                html.Div(
                    [
                        dbc.NavLink(
                            [html.I(className="fas fa-undo-alt"), html.Span("Back")],
                            href="/preprocessing",
                            id=ids.PREV_PAGE_LINK_ANALYZE,
                            className="process-nav-button process-nav-button--back",
                        ),
                        html.Div(className="process-footer-spacer"),
                    ],
                    className="process-footer",
                ),
            ],
            className="stage-card stage-card--analyze glass-panel",
        ),
    ],
    className="page-shell",
)
