import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

import eit_dash.definitions.element_ids as ids
import eit_dash.definitions.layout_styles as styles
from eit_dash.definitions.option_lists import FilterTypes, PeriodsSelectMethods, SynchMethods

register_page(__name__, path="/preprocessing")

resampling_card = html.Div(
    dbc.Card(
        [
            dbc.CardHeader("Resampling"),
            dbc.CardBody(id=ids.RESAMPLING_CARD_BODY),
            dbc.CardFooter(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Input(
                                type="number",
                                placeholder="Resampling frequency",
                                value=100,
                                id=ids.RESAMPLING_FREQUENCY_INPUT,
                            ),
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Apply",
                                id=ids.CONFIRM_RESAMPLING_BUTTON,
                                className="glass-button glass-button--primary w-100",
                            ),
                        ),
                    ],
                    className="g-3",
                ),
                style=styles.CARD_FOOTER,
            ),
        ],
        className="mini-card",
    ),
    id=ids.RESAMPLING_CARD,
)

summary = html.Div(
    [
        html.H2("Summary", style=styles.COLUMN_TITLE),
    ],
    className="workflow-section workflow-section--feature workflow-section--summary",
    id=ids.SUMMARY_COLUMN,
)

actions = html.Div(
    [
        html.H2("Pre-process", id=ids.PREPROCESING_TITLE, style=styles.COLUMN_TITLE),
        html.P(
            "Select the stable periods you want, preview the treatment on top of the raw signal, and confirm only the results you trust.",
            className="panel-copy",
        ),
        resampling_card,
        html.Div(className="compact-spacer"),
        html.Div(
            dbc.Button(
                "Synchronize data",
                id=ids.OPEN_SYNCH_BUTTON,
                disabled=True,
                className="glass-button glass-button--secondary w-100",
            ),
            hidden=True,
        ),
        html.Div(className="compact-spacer"),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Button(
                        "Select periods",
                        id=ids.OPEN_SELECT_PERIODS_BUTTON,
                        disabled=False,
                        className="glass-button glass-button--primary w-100",
                    ),
                ),
                dbc.Col(
                    dbc.Button(
                        "Filter data",
                        id=ids.OPEN_FILTER_DATA_BUTTON,
                        disabled=True,
                        className="glass-button glass-button--secondary w-100",
                    ),
                ),
            ],
            className="g-2",
        ),
    ],
    className="workflow-section workflow-section--feature",
)

results = html.Div(
    [
        html.H2("Selected periods", style=styles.COLUMN_TITLE),
        html.Div(
            [
                html.Div(id=ids.PREPROCESING_RESULTS_CONTAINER, style=styles.LOAD_RESULTS),
            ],
            className="glass-panel--results",
        ),
    ],
    className="workflow-section workflow-section--feature workflow-section--results",
)

modal_synchronization = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Data synchronization"), close_button=True),
                dbc.ModalBody(
                    [
                        dbc.Select(
                            id=ids.SYNC_METHOD_SELECTOR,
                            options=[{"label": method.name, "value": method.value} for method in SynchMethods],
                            value=str(SynchMethods.manual.value),
                        ),
                        html.Div(className="compact-spacer"),
                        dbc.Row(dbc.Checklist(id=ids.DATASET_SELECTION_CHECKBOX)),
                        html.Div(className="compact-spacer"),
                        dbc.Row(id=ids.SYNC_DATA_PREVIEW_CONTAINER),
                        dbc.Button(
                            "Sync Preview",
                            id=ids.CONFIRM_SYNCH_BUTTON,
                            className="glass-button glass-button--primary",
                        ),
                    ],
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id=ids.SYNCHRONIZATION_CONFIRM_BUTTON,
                        className="glass-button glass-button--ghost",
                        n_clicks=0,
                    ),
                ),
            ],
            id=ids.SYNCHRONIZATION_POPUP,
            centered=True,
            is_open=False,
            backdrop=False,
            scrollable=True,
            size="xl",
            className="glass-modal",
        ),
    ],
)

modal_selection_body = html.Div(
    [
        html.Div(id=ids.PERIODS_SELECTION_SELECT_DATASET),
        html.Div(className="compact-spacer"),
        dbc.Row(id=ids.PREPROCESING_SIGNALS_CHECKBOX_ROW),
        html.Div(className="compact-spacer"),
        dcc.Loading(
            html.Div(
                [
                    dbc.Row([dcc.Graph(id=ids.PREPROCESING_PERIODS_GRAPH, style=styles.EMPTY_ELEMENT)]),
                    html.H6("Period name", style=styles.SECTION_TITLE, className="mt-4"),
                    dbc.Input(
                        id=ids.PERIOD_NAME_INPUT,
                        placeholder="Enter period name (optional)...",
                        type="text",
                        className="mb-4 glass-input",
                    ),
                ],
                id=ids.PERIODS_SELECTION_DIV,
                hidden=True,
            ),
        ),
    ],
    id=ids.PERIODS_SELECTION_BODY,
)

modal_selection = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Periods selection"), close_button=True),
                dbc.ModalBody(
                    [
                        html.H6("Periods selection method", className="mb-2"),
                        dbc.Select(
                            id=ids.PERIODS_METHOD_SELECTOR,
                            options=[{"label": method.name, "value": method.value} for method in PeriodsSelectMethods],
                            value=str(PeriodsSelectMethods.Manual.value),
                            className="mb-3",
                        ),
                        modal_selection_body,
                    ],
                ),
                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Add selection",
                            id=ids.PREPROCESING_SELECT_BTN,
                            className="glass-button glass-button--secondary w-auto me-2",
                            size="sm",
                        ),
                        dbc.Button(
                            "Confirm",
                            id=ids.PERIODS_CONFIRM_BUTTON,
                            className="glass-button glass-button--primary w-auto",
                            n_clicks=0,
                            size="sm",
                        ),
                    ],
                ),
            ],
            id=ids.PERIODS_SELECTION_POPUP,
            centered=True,
            is_open=False,
            backdrop=False,
            scrollable=True,
            size="xl",
            className="glass-modal",
        ),
    ],
)

alert_filter = dbc.Alert([], id=ids.ALERT_FILTER, color="danger", dismissable=True, is_open=False, duration=3000)
alert_saved_results = dbc.Alert([], id=ids.ALERT_SAVED_RESULTS, color="success", dismissable=True, is_open=False, duration=3000)

filter_params = html.Div(
    [
        dbc.Row(alert_filter),
        dbc.Row(
            [
                dbc.Col([html.P("Filter Order"), dbc.Input(id=ids.FILTER_ORDER, type="number", min=0)]),
                dbc.Col([html.P("Cut off frequency low"), dbc.Input(id=ids.FILTER_CUTOFF_LOW, type="number", min=0)]),
                dbc.Col([html.P("Cut off frequency high"), dbc.Input(id=ids.FILTER_CUTOFF_HIGH, type="number", min=0)]),
            ],
            className="g-3",
        ),
        dbc.Row(
            [dbc.Col([dbc.Button("Apply", id=ids.FILTER_APPLY, disabled=True, className="glass-button glass-button--primary")])],
            style=styles.BUTTONS_ROW,
        ),
        dbc.Row(
            [
                html.Div(
                    [
                        html.H6("Select a period to view the results"),
                        dbc.Select(id=ids.FILTERING_SELECT_PERIOD_VIEW),
                        dcc.Graph(id=ids.FILTERING_RESULTS_GRAPH, style=styles.EMPTY_ELEMENT),
                    ],
                    id=ids.FILTERING_RESULTS_DIV,
                    hidden=True,
                ),
            ],
            style=styles.BUTTONS_ROW,
        ),
        dbc.Row(
            [
                html.Div(
                    [dbc.Button("Confirm", id=ids.FILTERING_CONFIRM_BUTTON, className="glass-button glass-button--primary")],
                    id=ids.FILTERING_CONFIRM_DIV,
                    hidden=True,
                ),
            ],
            style=styles.BUTTONS_ROW,
        ),
    ],
    id=ids.FILTER_PARAMS,
    hidden=True,
)

modal_filtering = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Filter"), close_button=True),
                dbc.ModalBody(
                    [
                        alert_saved_results,
                        html.H6("Select a filter"),
                        dbc.Select(
                            id=ids.FILTER_SELECTOR,
                            options=[{"label": filt.name, "value": filt.value} for filt in FilterTypes],
                        ),
                        html.Div(className="compact-spacer"),
                        filter_params,
                    ],
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close",
                        id=ids.FILTERING_CLOSE_BUTTON,
                        className="glass-button glass-button--ghost",
                        n_clicks=0,
                    ),
                ),
                html.Div(id=ids.UPDATE_FILTER_RESULTS, hidden=True),
            ],
            id=ids.FILTERING_SELECTION_POPUP,
            centered=True,
            is_open=False,
            backdrop=False,
            scrollable=True,
            size="xl",
            className="glass-modal",
        ),
    ],
)

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.P("Step 2 - Pre-processing", className="page-kicker"),
                        html.P(
                            "Narrow each dataset down to the periods that matter and compare your filtering decisions.",
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
                            href="/load",
                            id=ids.PREV_PAGE_LINK_PREP,
                            className="process-nav-button process-nav-button--back",
                        ),
                        dbc.NavLink(
                            [html.Span("Next"), html.I(className="fas fa-arrow-right")],
                            href="/analyze",
                            id=ids.NEXT_PAGE_LINK_PREP,
                            className="process-nav-button process-nav-button--next",
                        ),
                    ],
                    className="process-footer",
                ),
            ],
            className="stage-card stage-card--preprocess glass-panel",
        ),
        modal_synchronization,
        modal_selection,
        modal_filtering,
    ],
    className="page-shell",
)
