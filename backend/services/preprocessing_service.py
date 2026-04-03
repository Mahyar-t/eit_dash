from __future__ import annotations

from copy import deepcopy
from typing import Any

import plotly.graph_objects as go
from eitprocessing.datahandling.continuousdata import ContinuousData
from eitprocessing.filters.butterworth_filters import ButterworthFilter

from backend.state.session_store import SessionRecord, SessionStablePeriod
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
from eit_dash.definitions.option_lists import FilterTypes
from eit_dash.utils.common import (
    apply_figure_theme,
    create_slider_figure,
    get_selections_slidebar,
    get_signal_options,
    mark_selected_periods,
    update_figure_signal_visibility,
)
from eit_dash.utils.time_axis import build_time_axis_context


def build_preprocessing_state(record: SessionRecord) -> dict[str, Any]:
    return {
        'summary_datasets': [_serialize_dataset_summary_card(dataset) for dataset in record.loaded_datasets],
        'dataset_options': [
            {'label': dataset.label, 'value': index} for index, dataset in enumerate(record.loaded_datasets)
        ],
        'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
        'filter_card': _serialize_filter_card(record.saved_filter_params) if record.saved_filter_params else None,
        'can_select_periods': bool(record.loaded_datasets),
        'can_filter': bool(record.stable_periods),
    }


def build_period_preview(
    record: SessionRecord,
    dataset_index: int,
    selected_signals: list[int] | None = None,
) -> dict[str, Any]:
    dataset = record.loaded_datasets[dataset_index]
    options = get_signal_options(dataset, show_eit=True)
    preview_signals = list(dataset.continuous_data)
    figure = create_slider_figure(dataset, preview_signals)

    saved_periods = [period for period in record.stable_periods if period.dataset_index == dataset_index]
    if saved_periods:
        figure = mark_selected_periods(
            figure,
            saved_periods,
            _get_dataset_start_times(record, saved_periods),
        )

    if selected_signals is None:
        selected_signal_ids = [int(option['value']) for option in options]
    else:
        selected_signal_ids = [int(value) for value in selected_signals]

    selected_names = [str(option['label']) for option in options if int(option['value']) in set(selected_signal_ids)]
    figure = update_figure_signal_visibility(figure.to_dict(), selected_names)

    return {
        'dataset_index': dataset_index,
        'options': options,
        'selected_signals': selected_signal_ids,
        'figure': figure,
    }


def add_stable_period(
    record: SessionRecord,
    dataset_index: int,
    relayout_data: dict[str, Any] | None,
    selected_signals: list[int] | None,
    custom_name: str | None,
) -> dict[str, Any]:
    dataset = record.loaded_datasets[dataset_index]
    raw_signal = dataset.continuous_data[RAW_EIT_LABEL]

    if relayout_data is not None:
        start_sample, stop_sample = get_selections_slidebar(relayout_data)
        if not start_sample:
            start_sample = raw_signal.time[0]
        if not stop_sample:
            stop_sample = raw_signal.time[-1]
    else:
        start_sample = raw_signal.time[0]
        stop_sample = raw_signal.time[-1]

    period_index = _get_next_period_index(record)
    period_data = dataset.select_by_time(start_time=start_sample, end_time=stop_sample)
    period_data.label = custom_name.strip() if custom_name and custom_name.strip() else f'Period {period_index}'

    record.stable_periods.append(
        SessionStablePeriod(sequence=period_data, dataset_index=dataset_index, period_index=period_index),
    )
    record.reset_analyze_state()

    preview = build_period_preview(record, dataset_index, selected_signals)

    return {
        'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
        'can_filter': True,
        'period_preview': preview,
    }


def remove_stable_period(record: SessionRecord, period_index: int) -> dict[str, Any]:
    record.stable_periods = [period for period in record.stable_periods if period.period_index != period_index]
    record.temp_filtered_periods = [period for period in record.temp_filtered_periods if period.period_index != period_index]
    record.reset_analyze_state()

    if not record.stable_periods:
        record.saved_filter_params = None

    return {
        'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
        'filter_card': _serialize_filter_card(record.saved_filter_params) if record.saved_filter_params else None,
        'can_filter': bool(record.stable_periods),
    }


def apply_filter_preview(
    record: SessionRecord,
    filter_type: int,
    cutoff_low: float | None,
    cutoff_high: float | None,
    order: int,
) -> dict[str, Any]:
    params = _get_selected_parameters(cutoff_high, cutoff_low, order, filter_type)
    record.temp_filtered_periods = []

    for period in record.stable_periods:
        tmp_sequence = deepcopy(period.sequence)
        filtered_data = _filter_data(tmp_sequence, params)
        tmp_sequence.continuous_data.add(filtered_data)
        record.temp_filtered_periods.append(
            SessionStablePeriod(
                sequence=tmp_sequence,
                dataset_index=period.dataset_index,
                period_index=period.period_index,
            ),
        )

    return {
        'period_options': [
            {'label': filtered_period.sequence.label, 'value': filtered_period.period_index}
            for filtered_period in record.temp_filtered_periods
        ],
        'confirm_enabled': bool(record.temp_filtered_periods),
    }


def build_filtered_period_preview(record: SessionRecord, period_index: int) -> dict[str, Any]:
    original_period = _get_period(record.stable_periods, period_index)
    filtered_period = _get_period(record.temp_filtered_periods, period_index)

    original_data = original_period.sequence
    filtered_data = filtered_period.sequence
    dataset_start_time = _get_signal_start_time(record.loaded_datasets[original_period.dataset_index])
    selection_start_time = _get_signal_start_time(original_data)

    original_time_context = build_time_axis_context(
        original_data.continuous_data[RAW_EIT_LABEL].time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
    )
    filtered_time_context = build_time_axis_context(
        filtered_data.continuous_data[FILTERED_EIT_LABEL].time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
    )

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=original_time_context.x,
            y=original_data.continuous_data[RAW_EIT_LABEL].values,
            customdata=original_time_context.customdata,
            hovertemplate=original_time_context.hovertemplate,
            name='Original signal',
        ),
    )
    figure.add_trace(
        go.Scatter(
            x=filtered_time_context.x,
            y=filtered_data.continuous_data[FILTERED_EIT_LABEL].values,
            customdata=filtered_time_context.customdata,
            hovertemplate=filtered_time_context.hovertemplate,
            name='Filtered signal',
        ),
    )
    figure.update_xaxes(title_text=original_time_context.axis_title)

    return {'figure': apply_figure_theme(figure).to_dict()}


def confirm_filter_preview(record: SessionRecord) -> dict[str, Any]:
    if not record.temp_filtered_periods:
        return {
            'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
            'filter_card': _serialize_filter_card(record.saved_filter_params) if record.saved_filter_params else None,
        }

    updated_periods: list[SessionStablePeriod] = []
    temp_by_index = {period.period_index: period for period in record.temp_filtered_periods}
    for period in record.stable_periods:
        updated_periods.append(temp_by_index.get(period.period_index, period))

    record.stable_periods = updated_periods
    record.temp_filtered_periods = []
    record.reset_analyze_state()

    filter_params = None
    for period in record.stable_periods:
        filtered_series = period.sequence.continuous_data.get(FILTERED_EIT_LABEL)
        if filtered_series is not None:
            filter_params = filtered_series.parameters
            break

    record.saved_filter_params = filter_params
    return {
        'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
        'filter_card': _serialize_filter_card(record.saved_filter_params) if record.saved_filter_params else None,
    }


def cancel_filter_preview(record: SessionRecord) -> dict[str, Any]:
    record.temp_filtered_periods = []
    return {
        'period_options': [],
        'confirm_enabled': False,
    }


def remove_saved_filter(record: SessionRecord) -> dict[str, Any]:
    record.temp_filtered_periods = []
    record.saved_filter_params = None
    record.reset_analyze_state()
    for period in record.stable_periods:
        if period.sequence.continuous_data.get(FILTERED_EIT_LABEL):
            period.sequence.continuous_data.pop(FILTERED_EIT_LABEL)

    return {
        'selected_periods': [_serialize_period_card(record, period) for period in record.stable_periods],
        'filter_card': None,
    }


def _serialize_dataset_summary_card(dataset) -> dict[str, Any]:
    vendor_val = getattr(dataset.eit_data['raw'].vendor, 'value', str(dataset.eit_data['raw'].vendor))
    return {
        'label': dataset.label,
        'title': dataset.label,
        'rows': [
            {'label': 'Name', 'value': dataset.label},
            {'label': 'Frames', 'value': dataset.eit_data['raw'].nframes},
            {'label': 'Start time', 'value': f"{dataset.eit_data['raw'].time[0]:.3f} s"},
            {'label': 'End time', 'value': f"{dataset.eit_data['raw'].time[-1]:.3f} s"},
            {'label': 'Vendor', 'value': vendor_val},
            {'label': 'Signals', 'value': ', '.join(list(dataset.continuous_data))},
            {'label': 'Path', 'value': str(dataset.eit_data['raw'].path)},
        ],
    }


def _serialize_period_card(record: SessionRecord, period: SessionStablePeriod) -> dict[str, Any]:
    dataset_name = record.loaded_datasets[period.dataset_index].label
    return {
        'label': str(period.period_index),
        'title': period.sequence.label,
        'rows': [
            {'label': 'Name', 'value': period.sequence.label},
            {'label': 'Frames', 'value': period.sequence.eit_data['raw'].nframes},
            {'label': 'Start time', 'value': f"{period.sequence.eit_data['raw'].time[0]:.3f} s"},
            {'label': 'End time', 'value': f"{period.sequence.eit_data['raw'].time[-1]:.3f} s"},
            {'label': 'Dataset', 'value': dataset_name},
        ],
    }


def _serialize_filter_card(parameters: dict[str, Any] | None) -> dict[str, Any] | None:
    if not parameters:
        return None
    return {
        'label': 'filter-results',
        'title': 'Data filtered',
        'rows': [
            {'label': 'Filter type', 'value': parameters.get('filter_type', '')},
            {'label': 'Cutoff frequency', 'value': parameters.get('cutoff_frequency', '')},
            {'label': 'Order', 'value': parameters.get('order', '')},
            {'label': 'Sample frequency', 'value': parameters.get('sample_frequency', '')},
        ],
    }


def _get_signal_start_time(sequence, signal_label: str = RAW_EIT_LABEL) -> float:
    return float(sequence.continuous_data[signal_label].time[0])


def _get_dataset_start_times(record: SessionRecord, periods: list[SessionStablePeriod]) -> dict[int, float]:
    return {
        period.period_index: _get_signal_start_time(record.loaded_datasets[period.dataset_index])
        for period in periods
    }


def _get_next_period_index(record: SessionRecord) -> int:
    available_indexes = [period.period_index for period in record.stable_periods]
    return max(available_indexes) + 1 if available_indexes else 0


def _get_period(periods: list[SessionStablePeriod], period_index: int) -> SessionStablePeriod:
    for period in periods:
        if period.period_index == period_index:
            return period
    msg = f'Period with index {period_index} not found'
    raise ValueError(msg)


def _get_selected_parameters(co_high, co_low, order, filter_selected) -> dict[str, Any]:
    if co_high is None:
        cutoff_frequency = co_low
    elif co_low is None:
        cutoff_frequency = co_high
    else:
        cutoff_frequency = [co_low, co_high]

    return {
        'filter_type': FilterTypes(int(filter_selected)).name,
        'cutoff_frequency': cutoff_frequency,
        'order': order,
    }


def _filter_data(data, filter_params: dict[str, Any]) -> ContinuousData:
    raw_eit = data.eit_data.data['raw']
    sample_frequency = getattr(raw_eit, 'sample_frequency', None) or raw_eit.framerate
    filter_definition = {**filter_params, 'sample_frequency': sample_frequency}
    filt = ButterworthFilter(**filter_definition)
    gi = data.continuous_data[RAW_EIT_LABEL]

    return ContinuousData(
        FILTERED_EIT_LABEL,
        f"global_impedance filtered with {filter_definition['filter_type']}",
        'a.u.',
        'impedance',
        derived_from=[*gi.derived_from, gi],
        parameters=filter_definition,
        sample_frequency=sample_frequency,
        time=gi.time,
        values=filt.apply_filter(gi.values),
    )
