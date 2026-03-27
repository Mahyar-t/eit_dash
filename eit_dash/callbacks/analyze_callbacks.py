import contextlib

import numpy as np
from dash import ClientsideFunction, Input, MATCH, Output, State, callback, clientside_callback, ctx
from dash.exceptions import MissingCallbackContextException

from eitprocessing.parameters.eeli import EELI
import eit_dash.definitions.element_ids as ids
from eit_dash.app import data_object
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
from eit_dash.utils.common import (
    create_filter_results_card,
    create_info_card,
    create_selected_period_card,
)
from eit_dash.utils.output_rendering import _build_map_animation_figure, render_sequence_outputs

# ---------------------------------------------------------------------------
# Clientside callback: Play/Pause toggle + Reset for each EIT frame graph.
#
# Each graph instance has pattern-matched IDs keyed on {period, label}.
# The callback:
#   1. Toggles is_playing in the dcc.Store
#   2. Updates the button label (▶ Play <-> ⏸ Pause)
#   3. Calls Plotly.animate() on the graph to start/stop/reset animation
# ---------------------------------------------------------------------------
clientside_callback(
    ClientsideFunction(namespace="playback", function_name="control_animation"),
    Output({"type": ids.ANALYZE_EIT_PLAY_STATE, "period": MATCH, "label": MATCH}, "data"),
    Output({"type": ids.ANALYZE_EIT_PLAY_BTN, "period": MATCH, "label": MATCH}, "children"),
    Input({"type": ids.ANALYZE_EIT_PLAY_BTN, "period": MATCH, "label": MATCH}, "n_clicks"),
    Input({"type": ids.ANALYZE_EIT_RESET_BTN, "period": MATCH, "label": MATCH}, "n_clicks"),
    State({"type": ids.ANALYZE_EIT_PLAY_STATE, "period": MATCH, "label": MATCH}, "data"),
    State({"type": ids.ANALYZE_EIT_FRAME_GRAPH, "period": MATCH, "label": MATCH}, "id"),
    prevent_initial_call=True,
)


# ruff: noqa: ERA001
eeli = []


def _get_triggered_id():
    try:
        return ctx.triggered_id
    except MissingCallbackContextException:
        return None


def _select_signal(sequence):
    signal_label = FILTERED_EIT_LABEL if sequence.continuous_data.get(FILTERED_EIT_LABEL) else RAW_EIT_LABEL
    return sequence.continuous_data.get(signal_label)


def _ensure_signal_sample_frequency(sequence, signal):
    """Backfill missing sampling rate on derived signals using the raw EIT metadata."""
    if signal.sample_frequency is not None:
        return signal

    raw_eit = sequence.eit_data["raw"]
    sample_frequency = getattr(raw_eit, "sample_frequency", None)
    if sample_frequency is None:
        sample_frequency = raw_eit.framerate

    signal.sample_frequency = sample_frequency
    return signal


def _build_eeli_result(period_index: int, signal, eeli_data) -> dict:
    values = np.asarray(eeli_data.values)
    return {
        "index": period_index,
        "time": np.asarray(eeli_data.time),
        "values": values,
        "indices": np.searchsorted(signal.time, eeli_data.time),
        "mean": float(np.mean(values)) if len(values) else None,
        "median": float(np.median(values)) if len(values) else None,
        "standard deviation": float(np.std(values)) if len(values) else None,
    }


def _upsert_sparse_result(sequence, sparse_data) -> None:
    with contextlib.suppress(KeyError):
        sequence.sparse_data.pop(sparse_data.label)
    sequence.sparse_data.add(sparse_data)


@callback(
    Output(ids.SUMMARY_COLUMN_ANALYZE, "children", allow_duplicate=True),
    Output(ids.ANALYZE_SELECT_PERIOD_VIEW, "options"),
    [
        Input(ids.ANALYZE_RESULTS_TITLE, "children"),
    ],
    [
        State(ids.SUMMARY_COLUMN_ANALYZE, "children"),
    ],
    prevent_initial_call="initial_duplicate",
)
def page_setup(_, summary):
    """Set up the analyze page summary and available period options."""
    trigger = ctx.triggered_id
    options = []

    if trigger is None:
        for dataset in data_object.get_all_sequences():
            summary += [create_info_card(dataset)]

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
            options.append({"label": f"Period {period.get_period_index()}", "value": period.get_period_index()})

            if not filter_params:
                try:
                    filter_params = period.get_data().continuous_data.data[FILTERED_EIT_LABEL].parameters
                except KeyError:
                    contextlib.suppress(Exception)

        if filter_params:
            summary += [create_filter_results_card(filter_params)]

    return summary, options


@callback(
    Output(ids.ALERT_EELI, "is_open"),
    Output(ids.ALERT_EELI, "children"),
    Output(ids.ALERT_EELI, "color"),
    Input(ids.EELI_APPLY, "n_clicks"),
    State(ids.ANALYZE_SELECT_PERIOD_VIEW, "value"),
    prevent_initial_call=True,
)
def apply_eeli(_, selected):
    """Apply EELI, persist the result in each period sequence, and keep a plotting cache."""
    if selected is None:
        return True, "Select a period before applying EELI.", "warning"

    global eeli  # noqa: PLW0603

    eeli.clear()

    try:
        for period in data_object.get_all_stable_periods():
            sequence = period.get_data()
            signal = _ensure_signal_sample_frequency(sequence, _select_signal(sequence))
            eeli_data = EELI().compute_parameter(signal)
            _upsert_sparse_result(sequence, eeli_data)
            eeli.append(_build_eeli_result(period.get_period_index(), signal, eeli_data))
    except Exception as exc:  # pragma: no cover - defensive UI guard
        eeli.clear()
        return True, f"EELI failed: {exc}", "danger"

    return True, f"EELI applied to {len(eeli)} period(s).", "success"


@callback(
    Output(ids.ANALYZE_OUTPUTS_CONTAINER, "children"),
    Input(ids.ANALYZE_SELECT_PERIOD_VIEW, "value"),
    Input(ids.EELI_APPLY, "n_clicks"),
)
def show_outputs(selected, _):
    """Render all outputs currently stored in the selected period sequence."""
    if selected is None or _get_triggered_id() != ids.EELI_APPLY:
        return []

    period = data_object.get_stable_period(int(selected))
    sequence = period.get_data()
    source_dataset = data_object.get_sequence_at(period.get_dataset_index())
    return render_sequence_outputs(sequence, source_dataset, int(selected))


@callback(
    Output({"type": ids.ANALYZE_EIT_FRAME_GRAPH, "period": MATCH, "label": MATCH}, "figure"),
    Input({"type": ids.ANALYZE_EIT_FRAME_COUNT_INPUT, "period": MATCH, "label": MATCH}, "value"),
    State({"type": ids.ANALYZE_EIT_FRAME_GRAPH, "period": MATCH, "label": MATCH}, "id"),
    prevent_initial_call=True,
)
def update_eit_frame_playback(frame_count, graph_id):
    """Update the EIT frame playback figure with the requested number of displayed frames."""
    period = data_object.get_stable_period(int(graph_id["period"]))
    eit_data = period.get_data().eit_data[graph_id["label"]]
    return _build_map_animation_figure(eit_data.pixel_impedance, eit_data.time, "Frame playback", max_frames=frame_count)
