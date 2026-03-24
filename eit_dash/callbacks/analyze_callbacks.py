import contextlib

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dash import Input, Output, State, callback, ctx
from dash.exceptions import PreventUpdate

from eitprocessing.parameters.eeli import EELI
import eit_dash.definitions.element_ids as ids
import eit_dash.definitions.layout_styles as styles
from eit_dash.app import data_object
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
from eit_dash.utils.common import (
    apply_figure_theme,
    create_filter_results_card,
    create_info_card,
    create_selected_period_card,
)
from eit_dash.utils.time_axis import build_time_axis_context

# ruff: noqa: ERA001
eeli = []


@callback(
    Output(ids.SUMMARY_COLUMN_ANALYZE, "children", allow_duplicate=True),
    Output(ids.ANALYZE_SELECT_PERIOD_VIEW, "options"),
    [
        Input(ids.ANALYZE_RESULTS_TITLE, "children"),
    ],
    [
        State(ids.SUMMARY_COLUMN_ANALYZE, "children"),
    ],
    # this allows duplicate outputs with initial call
    prevent_initial_call="initial_duplicate",
)
def page_setup(_, summary):
    """Setups the page elements when it starts up.

    When the page is loaded, it populates the summary column
    with the info about the loaded datasets and the preprocessing steps.
    Populates the periods selections element with the loaded periods.
    """
    trigger = ctx.triggered_id
    options = []

    if trigger is None:
        for d in data_object.get_all_sequences():
            card = create_info_card(d)
            summary += [card]

        filter_params = {}

        for period in data_object.get_all_stable_periods():
            summary += [
                create_selected_period_card(
                    period.get_data(),
                    period.get_dataset_index(),
                    period.get_period_index(),
                    False,
                ),
            ]

            # populate period selection
            options.append(
                {
                    "label": f"Period {period.get_period_index()}",
                    "value": period.get_period_index(),
                },
            )

            if not filter_params:
                try:
                    filter_params = period.get_data().continuous_data.data[FILTERED_EIT_LABEL].parameters
                except KeyError:
                    contextlib.suppress(Exception)
        if filter_params:
            summary += [create_filter_results_card(filter_params)]

    return summary, options


@callback(
    Output(ids.EELI_RESULTS_GRAPH_DIV, "hidden"),
    Output(ids.ALERT_EELI, "is_open"),
    Output(ids.ALERT_EELI, "children"),
    Output(ids.ALERT_EELI, "color"),
    Input(ids.EELI_APPLY, "n_clicks"),
    State(ids.ANALYZE_SELECT_PERIOD_VIEW, "value"),
    prevent_initial_call=True,
)
def apply_eeli(_, selected):
    """Apply EELI and store results."""
    if selected is None:
        return True, True, "Select a period before applying EELI.", "warning"

    global eeli  # noqa: PLW0603

    eeli.clear()

    try:
        for period in data_object.get_all_stable_periods():
            sequence = period.get_data()
            signal_label = FILTERED_EIT_LABEL if sequence.continuous_data.get(FILTERED_EIT_LABEL) else RAW_EIT_LABEL
            signal = sequence.continuous_data.get(signal_label)
            eeli_data = EELI().compute_parameter(signal)

            eeli_result = {
                "index": period.get_period_index(),
                "time": np.asarray(eeli_data.time),
                "values": np.asarray(eeli_data.values),
                "indices": np.searchsorted(signal.time, eeli_data.time),
                "mean": float(np.mean(eeli_data.values)) if len(eeli_data.values) else None,
                "median": float(np.median(eeli_data.values)) if len(eeli_data.values) else None,
                "standard deviation": float(np.std(eeli_data.values)) if len(eeli_data.values) else None,
            }
            eeli.append(eeli_result)
    except Exception as exc:  # pragma: no cover - defensive UI guard
        eeli.clear()
        return True, True, f"EELI failed: {exc}", "danger"

    return False, True, f"EELI applied to {len(eeli)} period(s).", "success"


@callback(
    [
        Output(ids.EELI_RESULTS_GRAPH, "figure"),
        Output(ids.EELI_RESULTS_GRAPH, "style"),
    ],
    Input(ids.ANALYZE_SELECT_PERIOD_VIEW, "value"),
    Input(ids.EELI_APPLY, "n_clicks"),
    prevent_initial_call=True,
)
def show_eeli(selected, _):
    """Show the results of the EELI for the selected period."""
    if selected is None:
        raise PreventUpdate

    period = data_object.get_stable_period(int(selected))
    sequence = period.get_data()
    source_dataset = data_object.get_sequence_at(period.get_dataset_index())

    # Find the matching EELI result (may not exist if EELI hasn't been computed)
    result = None
    for e in eeli:
        if e["index"] == int(selected):
            result = e
            break

    if sequence.continuous_data.get(FILTERED_EIT_LABEL):
        data = sequence.continuous_data.get(FILTERED_EIT_LABEL)
    else:
        data = sequence.continuous_data.get(RAW_EIT_LABEL)

    dataset_start_time = float(source_dataset.continuous_data[RAW_EIT_LABEL].time[0])
    selection_start_time = float(data.time[0])
    signal_time_context = build_time_axis_context(
        data.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
    )

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.2,
        row_heights=[0.62, 0.38],
    )

    figure.add_trace(
        go.Scatter(
            x=signal_time_context.x,
            y=data.values,
            customdata=signal_time_context.customdata,
            hovertemplate=signal_time_context.hovertemplate,
            name="Input signal",
            line={"color": "#38bdf8", "width": 2},
            showlegend=True,
        ),
        row=1,
        col=1,
    )

    figure.update_layout(
        yaxis={"title": data.label or "Signal before EELI"},
        yaxis2={"title": "EELI (a.u.)", "color": "#ef4444"},
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
    )

    eeli_x = []
    eeli_y = []
    has_eeli_results = result is not None and len(result["values"]) > 0

    if has_eeli_results:
        eeli_time_context = build_time_axis_context(
            result["time"],
            dataset_start_time=dataset_start_time,
            selection_start_time=selection_start_time,
        )
        eeli_x = eeli_time_context.x
        eeli_y = result["values"]

        if result["mean"] is not None:
            figure.add_trace(
                go.Scatter(
                    x=signal_time_context.x,
                    y=[result["mean"]] * len(data.time),
                    customdata=signal_time_context.customdata,
                    hovertemplate=signal_time_context.hovertemplate,
                    mode="lines",
                    line={"color": "#991b1b", "width": 1.5, "dash": "dash"},
                    name="EELI mean",
                    showlegend=True,
                ),
                row=2,
                col=1,
            )
        if result["median"] is not None:
            figure.add_trace(
                go.Scatter(
                    x=signal_time_context.x,
                    y=[result["median"]] * len(data.time),
                    customdata=signal_time_context.customdata,
                    hovertemplate=signal_time_context.hovertemplate,
                    mode="lines",
                    line={"color": "#dc2626", "width": 1.5, "dash": "dot"},
                    name="EELI median",
                    showlegend=True,
                ),
                row=2,
                col=1,
            )

        if result["standard deviation"] is not None and result["mean"] is not None:
            sd_upper = result["mean"] + result["standard deviation"]
            sd_lower = result["mean"] - result["standard deviation"]

            figure.add_trace(
                go.Scatter(
                    x=signal_time_context.x,
                    y=[sd_upper] * len(data.time),
                    customdata=signal_time_context.customdata,
                    hovertemplate=signal_time_context.hovertemplate,
                    fill=None,
                    mode="lines",
                    line={"color": "rgba(239,68,68,0)"},
                    name="Standard deviation band",
                    showlegend=False,
                ),
                row=2,
                col=1,
            )

            figure.add_trace(
                go.Scatter(
                    x=signal_time_context.x,
                    y=[sd_lower] * len(data.time),
                    customdata=signal_time_context.customdata,
                    hovertemplate=signal_time_context.hovertemplate,
                    fill="tonexty",
                    mode="lines",
                    line={"color": "rgba(239,68,68,0.25)"},
                    fillcolor="rgba(239,68,68,0.12)",
                    name="Standard deviation band",
                    showlegend=True,
                ),
                row=2,
                col=1,
            )

        figure.add_trace(
            go.Scatter(
                x=eeli_x,
                y=eeli_y,
                customdata=eeli_time_context.customdata,
                hovertemplate=eeli_time_context.hovertemplate,
                line={"color": "#ef4444", "width": 1.5},
                marker={"color": "#ef4444", "size": 8},
                name="EELI results",
                mode="lines+markers",
                showlegend=True,
            ),
            row=2,
            col=1,
        )
    else:
        figure.add_trace(
            go.Scatter(
                x=[],
                y=[],
                name="EELI results",
                mode="lines",
                line={"color": "#ef4444", "width": 1.5},
                showlegend=False,
                hoverinfo="skip",
            ),
            row=2,
            col=1,
        )

    figure.update_xaxes(title_text=signal_time_context.axis_title, row=2, col=1, rangeslider_visible=False)

    return apply_figure_theme(figure), styles.GRAPH
