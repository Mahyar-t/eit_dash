from pathlib import Path

import dash_bootstrap_components as dbc
from dash import dcc, html, register_page

import eit_dash.definitions.element_ids as ids
import eit_dash.definitions.layout_styles as styles
from eit_dash.definitions.option_lists import InputFiletypes

register_page(__name__, path="/load")



input_type_selector = html.Div(
    [
        html.Div(
            [
                html.Div(
                    dbc.Select(
                        id=ids.INPUT_TYPE_SELECTOR,
                        options=[{"label": filetype.name, "value": filetype.value} for filetype in InputFiletypes],
                        value=str(InputFiletypes.Sentec.value),
                        className="form-select",
                    ),
                    style={"flex": "8"},
                ),
                html.Div(
                    dbc.Button(
                        "Select Files",
                        id=ids.SELECT_FILES_BUTTON,
                        className="glass-button glass-button--primary w-100",
                    ),
                    style={"flex": "2"},
                ),
            ],
            className="d-flex gap-3",
        ),
        dbc.Row(dbc.Label(id=ids.METADATA, className="field-meta")),
    ],
    className="action-stack mt-3",
)

add_data_selector = dcc.Loading(
    html.Div(
        id=ids.DATA_SELECTOR_OPTIONS,
        hidden=True,
        children=[
            html.H5("Pre-selection", style=styles.SECTION_TITLE),
            dcc.Graph(id=ids.FILE_LENGTH_SLIDER),
            html.H5("Signal selections", style=styles.SECTION_TITLE, className="mt-4"),
            dbc.Row(
                dcc.Checklist(
                    id=ids.CHECKBOX_SIGNALS,
                    inputStyle=styles.CHECKBOX_INPUT,
                    className="signal-checklist",
                ),
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Button(
                            "Cancel",
                            id=ids.LOAD_CANCEL_BUTTON,
                            className="glass-button glass-button--ghost w-100",
                            color="danger",
                            n_clicks=0,
                        ),
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Confirm",
                            id=ids.LOAD_CONFIRM_BUTTON,
                            className="glass-button glass-button--primary w-100",
                            color="success",
                            n_clicks=0,
                        ),
                    ),
                ],
                style=styles.BUTTONS_ROW,
                className="g-3",
            ),
        ],
    ),
)

results = html.Div(
    [
        html.H2("Data Preview", id=ids.LOAD_RESULTS_TITLE, style=styles.COLUMN_TITLE),
        html.Div(
            [
                add_data_selector,
                html.Div(id=ids.DATASET_CONTAINER, style=styles.LOAD_RESULTS),
            ],
            className="glass-panel--results",
        ),
    ],
    className="workflow-section workflow-section--feature workflow-section--results",
)

actions = html.Div(
    [
        html.H1("Load Datasets", className="page-kicker"),
        html.P(
            "Choose a vendor format, preview the recording, and cut the imported file into datasets you want to keep.",
            className="page-intro",
        ),
        input_type_selector,
    ],
    className="workflow-section workflow-section--feature",
)

placeholder_nfiles = html.Div(hidden=True, id=ids.NFILES_PLACEHOLDER, children=0)

file_browser = html.Div(
    [
        dbc.Row(
            [
                dcc.Store(id=ids.STORED_CWD, data=str(Path.cwd())),
                dbc.Button(
                    [
                        html.I(className="fas fa-level-up-alt me-2"),
                        "Parent Directory",
                    ],
                    id=ids.PARENT_DIR,
                    className="glass-button glass-button--secondary mb-4 mx-2",
                    style={"width": "auto"},
                ),
                html.Div(html.Code(str(Path.cwd()), id=ids.CWD), style={"display": "none"}),
                html.Div(id=ids.CWD_FILES, style=styles.FILE_BROWSER, className="browser-list gap-3"),
            ],
        ),
    ],
)

alert_load = dbc.Alert(
    "The selected file cannot be loaded",
    id=ids.ALERT_LOAD,
    color="primary",
    dismissable=True,
    is_open=False,
    duration=3000,
)

modal_dialog = html.Div(
    [
        dcc.Loading(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Select a file"), close_button=True),
                        dbc.ModalBody([alert_load, file_browser]),
                    ],
                    id=ids.CHOOSE_DATA_POPUP,
                    centered=True,
                    is_open=False,
                    backdrop=False,
                    scrollable=True,
                    className="glass-modal",
                    size="xl",
                ),
            ],
        ),
    ],
)

populate_loaded_data = html.Div(id=ids.POPULATE_DATA)

layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.P("Step 1 - Load Data", className="page-kicker"),
                        html.P(
                            "Bring in a local file, inspect the available channels, and prepare a clean set of datasets for the next stage. Loaded datasets and selections will appear here.",
                            className="page-intro",
                        ),
                    ],
                    className="page-hero",
                ),
                html.Div([actions, results], className="workflow-board"),
                html.Div(
                    [
                        html.Div(className="process-footer-spacer"),
                        dbc.NavLink(
                            [html.Span("Next"), html.I(className="fas fa-arrow-right")],
                            href="/preprocessing",
                            id=ids.NEXT_PAGE_LINK_LOAD,
                            className="process-nav-button process-nav-button--next",
                        ),
                    ],
                    className="process-footer",
                ),
            ],
            className="stage-card stage-card--load glass-panel",
        ),
        placeholder_nfiles,
        modal_dialog,
        populate_loaded_data,
    ],
    className="page-shell",
)
