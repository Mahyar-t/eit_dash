from __future__ import annotations

import contextlib
import json
from typing import Any

import numpy as np
import plotly.graph_objects as go
from eitprocessing.features.breath_detection import BreathDetection
from eitprocessing.parameters.eeli import EELI
from eitprocessing.parameters.tidal_impedance_variation import TIV

from backend.services.load_service import serialize_dataset
from backend.services.preprocessing_service import _serialize_filter_card, _serialize_period_card
from backend.state.session_store import SessionRecord, SessionStablePeriod
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
from eit_dash.utils.common import apply_figure_theme
from eit_dash.utils.output_rendering import (
    _build_continuous_figure,
    _build_eit_signal_figure,
    _build_map_animation_figure,
    _build_sparse_numeric_figure,
    _collection_items,
    _default_animation_frame_count,
    _get_dataset_start_time,
    _get_selection_start_time,
    _interval_rows,
    _numeric_summary_rows,
    _sparse_preview_rows,
    _sparse_rows_without_values,
    _values_are_2d_maps,
    _values_are_numeric_scalars,
)
from eit_dash.utils.time_axis import build_time_axis_context


_ANALYZE_SPARSE_LABEL = 'continuous_eelis'
_ANALYZE_SPARSE_TITLE = 'EELI'
_HIDDEN_SPARSE_LABELS = {
    'minvalues_(draeger)',
    'maxvalues_(draeger)',
    'events_(draeger)',
}


def build_analyze_state(record: SessionRecord) -> dict[str, Any]:
    summary_cards = [serialize_dataset(dataset) for dataset in record.loaded_datasets]
    summary_cards.extend(_serialize_period_card(record, period) for period in record.stable_periods)

    if record.saved_filter_params:
        summary_cards.append(_serialize_filter_card(record.saved_filter_params))

    period_options = [
        {'label': f'Period {period.period_index}', 'value': period.period_index}
        for period in record.stable_periods
    ]

    selected_period = _select_active_period(record, period_options)
    return {
        'summary_cards': summary_cards,
        'period_options': period_options,
        'selected_period': selected_period,
        'can_calculate': bool(period_options),
        'has_results': bool(record.analyze_eeli_results),
    }


def calculate_results(record: SessionRecord, selected_period: int | None) -> dict[str, Any]:
    if selected_period is None:
        return {
            'alert': {
                'is_open': True,
                'message': 'Select a period before applying EELI.',
                'color': 'warning',
            },
            'results': None,
        }

    if not record.stable_periods:
        return {
            'alert': {
                'is_open': True,
                'message': 'No periods are available for analysis.',
                'color': 'warning',
            },
            'results': None,
        }

    record.selected_analyze_period_index = int(selected_period)
    record.analyze_eeli_results.clear()

    try:
        for period in record.stable_periods:
            sequence = period.sequence
            signal = _ensure_signal_sample_frequency(sequence, _select_signal(sequence))
            eeli_data = EELI().compute_parameter(signal)
            _upsert_sparse_result(sequence, eeli_data)
            record.analyze_eeli_results[period.period_index] = _build_eeli_result(period.period_index, signal, eeli_data)
    except Exception as exc:  # pragma: no cover - defensive API guard
        record.analyze_eeli_results.clear()
        return {
            'alert': {
                'is_open': True,
                'message': f'EELI failed: {exc}',
                'color': 'danger',
            },
            'results': None,
        }

    return {
        'alert': {
            'is_open': True,
            'message': f"EELI applied to {len(record.analyze_eeli_results)} period(s).",
            'color': 'success',
        },
        'results': build_analyze_results(record, int(selected_period)),
    }


def build_analyze_results(record: SessionRecord, period_index: int | None) -> dict[str, Any] | None:
    if period_index is None or not record.analyze_eeli_results:
        return None

    period = _get_period(record.stable_periods, int(period_index))
    record.selected_analyze_period_index = period.period_index

    sequence = period.sequence
    source_dataset = record.loaded_datasets[period.dataset_index]
    dataset_start_time = _get_dataset_start_time(sequence, source_dataset)
    selection_start_time = _get_selection_start_time(sequence)

    return {
        'period_index': period.period_index,
        'overview': _serialize_overview_card(sequence),
        'sections': [
            _serialize_eit_section(sequence, dataset_start_time, selection_start_time, period.period_index),
            _serialize_continuous_section(sequence, dataset_start_time, selection_start_time),
            _serialize_sparse_section(sequence, dataset_start_time, selection_start_time),
            _serialize_interval_section(sequence),
        ],
    }


def build_eit_frame_preview(record: SessionRecord, period_index: int, label: str, frame_count: int) -> dict[str, Any]:
    period = _get_period(record.stable_periods, int(period_index))
    eit_data = period.sequence.eit_data[label]
    effective_frame_count = max(1, min(int(frame_count), eit_data.nframes))
    figure = _build_map_animation_figure(
        eit_data.pixel_impedance,
        eit_data.time,
        'Frame playback',
        max_frames=effective_frame_count,
    )
    return {
        'figure': _serialize_figure(figure),
        'frame_count': effective_frame_count,
        'max_frame_count': eit_data.nframes,
    }


# --- Old analyze callback compatibility helpers ---------------------------------

def _select_signal(sequence):
    signal_label = FILTERED_EIT_LABEL if sequence.continuous_data.get(FILTERED_EIT_LABEL) else RAW_EIT_LABEL
    return sequence.continuous_data.get(signal_label)


def _ensure_signal_sample_frequency(sequence, signal):
    if signal.sample_frequency is not None:
        return signal

    raw_eit = sequence.eit_data['raw']
    sample_frequency = getattr(raw_eit, 'sample_frequency', None)
    if sample_frequency is None:
        sample_frequency = raw_eit.framerate

    signal.sample_frequency = sample_frequency
    return signal


def _build_eeli_result(period_index: int, signal, eeli_data) -> dict[str, Any]:
    values = np.asarray(eeli_data.values)
    return {
        'index': period_index,
        'time': np.asarray(eeli_data.time),
        'values': values,
        'indices': np.searchsorted(signal.time, eeli_data.time),
        'mean': float(np.mean(values)) if len(values) else None,
        'median': float(np.median(values)) if len(values) else None,
        'standard deviation': float(np.std(values)) if len(values) else None,
    }


def _upsert_sparse_result(sequence, sparse_data) -> None:
    with contextlib.suppress(KeyError):
        sequence.sparse_data.pop(sparse_data.label)
    sequence.sparse_data.add(sparse_data)


# --- Analyze response serialization ---------------------------------------------

def _serialize_overview_card(sequence) -> dict[str, Any]:
    return {
        'title': 'Output Overview',
        'tables': [
            _serialize_rows(
                [
                    ('Sequence', sequence.label),
                    ('EIT collections', len(sequence.eit_data)),
                    ('Continuous collections', len(sequence.continuous_data)),
                    ('Sparse collections', len(sequence.sparse_data)),
                    ('Interval collections', len(sequence.interval_data)),
                ],
            ),
        ],
        'figures': [],
    }


def _serialize_eit_section(sequence, dataset_start_time: float, selection_start_time: float, period_index: int) -> dict[str, Any]:
    items = []
    for label, eit_data in _collection_items(sequence.eit_data):
        default_frame_count = _default_animation_frame_count(eit_data.nframes)
        items.append(
            {
                'title': label,
                'tables': [
                    _serialize_rows(
                        [
                            ('Vendor', getattr(eit_data.vendor, 'value', str(eit_data.vendor))),
                            ('Frames', eit_data.nframes),
                            ('Shape', eit_data.pixel_impedance.shape),
                            ('Sample frequency', f'{eit_data.sample_frequency:.3f} Hz'),
                            ('Start time', f'{eit_data.time[0]:.3f} s'),
                            ('End time', f'{eit_data.time[-1]:.3f} s'),
                            ('Path', eit_data.path),
                        ],
                    ),
                ],
                'figures': [
                    {
                        'role': 'plot',
                        'figure': _serialize_figure(
                            _build_eit_signal_figure(eit_data, dataset_start_time, selection_start_time),
                        ),
                    },
                    {
                        'role': 'eit-playback',
                        'figure': _serialize_figure(
                            _build_map_animation_figure(
                                eit_data.pixel_impedance,
                                eit_data.time,
                                'Frame playback',
                            ),
                        ),
                        'playback': {
                            'period_index': period_index,
                            'label': label,
                            'frame_count': default_frame_count,
                            'max_frame_count': eit_data.nframes,
                        },
                        'height_px': 800,
                    },
                ],
            },
        )

    return {
        'title': f'EIT Data ({len(sequence.eit_data)})',
        'items': items,
        'empty_message': 'No EIT outputs available for this period.' if not items else None,
    }


def _serialize_continuous_section(sequence, dataset_start_time: float, selection_start_time: float) -> dict[str, Any]:
    items = []
    for label, data in _collection_items(sequence.continuous_data):
        if label not in {RAW_EIT_LABEL, FILTERED_EIT_LABEL}:
            continue

        items.append(
            {
                'title': label,
                'tables': [
                    _serialize_rows(
                        [
                            ('Name', data.name),
                            ('Category', data.category),
                            ('Unit', data.unit),
                            ('Samples', len(data)),
                            (
                                'Sample frequency',
                                f'{data.sample_frequency:.3f} Hz' if data.sample_frequency is not None else 'n/a',
                            ),
                            ('Start time', f'{data.time[0]:.3f} s'),
                            ('End time', f'{data.time[-1]:.3f} s'),
                        ],
                    ),
                ],
                'figures': [
                    {
                        'role': 'plot',
                        'figure': _serialize_figure(
                            _build_continuous_figure(data, dataset_start_time, selection_start_time),
                        ),
                    },
                ],
            },
        )

    return {
        'title': f'Continuous Data ({len(items)})',
        'items': items,
        'empty_message': 'No continuous outputs available for this period.' if not items else None,
    }


def _serialize_sparse_section(sequence, dataset_start_time: float, selection_start_time: float) -> dict[str, Any]:
    items = []

    for label, data in _collection_items(sequence.sparse_data):
        if _should_hide_sparse_artifact(label):
            continue

        card = {
            'title': _ANALYZE_SPARSE_TITLE if label == _ANALYZE_SPARSE_LABEL else label,
            'tables': [
                _serialize_rows(
                    [
                        ('Name', data.name),
                        ('Category', data.category),
                        ('Unit', data.unit),
                        ('Events', len(data)),
                    ],
                ),
            ],
            'figures': [],
        }

        if not data.has_values:
            card['tables'].append(_serialize_rows(_sparse_rows_without_values(data)))
        elif _values_are_numeric_scalars(data.values):
            card['figures'].append(
                {
                    'role': 'plot',
                    'figure': _serialize_figure(
                        _build_analyze_sparse_numeric_figure(sequence, label, data, dataset_start_time, selection_start_time),
                    ),
                },
            )
            card['tables'].append(_serialize_rows(_numeric_summary_rows(np.asarray(data.values, dtype=float))))
        elif _values_are_2d_maps(data.values):
            card['figures'].append(
                {
                    'role': 'animation',
                    'figure': _serialize_figure(
                        _build_map_animation_figure(np.asarray(data.values), data.time, 'Map playback'),
                    ),
                },
            )
            card['tables'].append(_serialize_rows(_sparse_preview_rows(data)))
        else:
            card['tables'].append(_serialize_rows(_sparse_preview_rows(data)))

        items.append(card)
        if label == _ANALYZE_SPARSE_LABEL:
            tiv_card = _build_tiv_card(sequence, dataset_start_time, selection_start_time)
            if tiv_card is not None:
                items.append(tiv_card)

    return {
        'title': f'Sparse Data ({len(items)})',
        'items': items,
        'empty_message': 'No sparse outputs available for this period.' if not items else None,
    }


def _serialize_interval_section(sequence) -> dict[str, Any]:
    items = []
    for label, data in _collection_items(sequence.interval_data):
        items.append(
            {
                'title': label,
                'tables': [
                    _serialize_rows(
                        [
                            ('Name', data.name),
                            ('Category', data.category),
                            ('Unit', data.unit),
                            ('Intervals', len(data)),
                        ],
                    ),
                    _serialize_rows(_interval_rows(data)),
                ],
                'figures': [],
            },
        )

    return {
        'title': f'Interval Data ({len(sequence.interval_data)})',
        'items': items,
        'empty_message': 'No interval outputs available for this period.' if not items else None,
    }


def _serialize_rows(rows: list[tuple[str, Any]]) -> list[dict[str, Any]]:
    return [{'label': str(label), 'value': str(value)} for label, value in rows]


def _serialize_figure(figure) -> dict[str, Any]:
    return json.loads(figure.to_json())


def _build_analyze_sparse_numeric_figure(sequence, label: str, data, dataset_start_time: float, selection_start_time: float):
    if label != _ANALYZE_SPARSE_LABEL:
        return _build_sparse_numeric_figure(data, dataset_start_time, selection_start_time)

    signal = _select_signal(sequence)
    if signal is None:
        return _build_sparse_numeric_figure(data, dataset_start_time, selection_start_time)

    values = np.asarray(data.values, dtype=float)
    if values.size == 0:
        return _build_sparse_numeric_figure(data, dataset_start_time, selection_start_time)

    signal_time_context = build_time_axis_context(
        signal.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Value: %{y:.3f}<extra></extra>",
    )
    sparse_time_context = build_time_axis_context(
        data.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Value: %{y:.3f}<extra></extra>",
    )

    mean_value = float(np.nanmean(values))
    median_value = float(np.nanmedian(values))
    std_value = float(np.nanstd(values))

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=signal_time_context.x,
            y=signal.values,
            customdata=signal_time_context.customdata,
            hovertemplate=signal_time_context.hovertemplate,
            name=signal.label,
            line={"color": "#22c55e", "width": 2},
        )
    )
    figure.add_trace(
        go.Scatter(
            x=sparse_time_context.x,
            y=values,
            customdata=sparse_time_context.customdata,
            hovertemplate=sparse_time_context.hovertemplate,
            mode="markers",
            marker={"size": 10, "color": "rgba(255, 0, 0, 1)"},
            name="EELIs",
        )
    )
    figure.add_hrect(
        y0=mean_value - std_value,
        y1=mean_value + std_value,
        fillcolor="rgba(0, 255, 255, 0.2)",
        line_width=0,
    )
    figure.add_hline(
        y=mean_value,
        line_color="rgba(0, 255, 255, 1)",
        line_width=2,
        name="Mean",
    )
    # Legend-only traces keep the legend entries visible without changing
    # the actual plot implementation based on hrect/hline.
    figure.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            name="Mean",
            line={"color": "rgba(0, 255, 255, 1)", "width": 2},
            hoverinfo="skip",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="lines",
            name="Standard deviation",
            line={"color": "rgba(0, 255, 255, 0.7)", "width": 8},
            hoverinfo="skip",
        )
    )
    figure.update_layout(
        title=data.name,
        xaxis={"title": signal_time_context.axis_title},
        yaxis={"title": f"{data.category} ({data.unit})" if data.unit else data.category},
        showlegend=True,
    )
    return apply_figure_theme(figure)


def _build_continuous_tiv_reference_figure(sequence, dataset_start_time: float, selection_start_time: float):
    signal = _select_signal(sequence)
    if signal is None:
        return go.Figure()

    breaths = BreathDetection().find_breaths(signal)
    tiv_data = TIV().compute_continuous_parameter(signal, store=False)

    signal_time_context = build_time_axis_context(
        signal.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Value: %{y:.3f}<extra></extra>",
    )

    breath_values = list(breaths.values)
    start_times = np.asarray([breath.start_time for breath in breath_values], dtype=float)
    middle_times = np.asarray([breath.middle_time for breath in breath_values], dtype=float)
    end_times = np.asarray([breath.end_time for breath in breath_values], dtype=float)

    start_indices = np.searchsorted(signal.time, start_times)
    middle_indices = np.searchsorted(signal.time, middle_times)
    end_indices = np.searchsorted(signal.time, end_times)

    max_index = len(signal.values) - 1
    start_indices = np.clip(start_indices, 0, max_index)
    middle_indices = np.clip(middle_indices, 0, max_index)
    end_indices = np.clip(end_indices, 0, max_index)

    tiv_times = np.asarray(tiv_data.time, dtype=float)
    tiv_values = np.asarray(tiv_data.values, dtype=float)
    tiv_indices = np.searchsorted(signal.time, tiv_times)
    tiv_indices = np.clip(tiv_indices, 0, max_index)
    tiv_top = np.asarray(signal.values, dtype=float)[tiv_indices]
    tiv_bottom = tiv_top - tiv_values

    tiv_x: list[float | None] = []
    tiv_y: list[float | None] = []
    for time_value, bottom_value, top_value in zip(tiv_times, tiv_bottom, tiv_top, strict=True):
        tiv_x.extend([float(time_value), float(time_value), None])
        tiv_y.extend([float(bottom_value), float(top_value), None])

    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=signal_time_context.x,
            y=signal.values,
            customdata=signal_time_context.customdata,
            hovertemplate=signal_time_context.hovertemplate,
            name=signal.label,
        )
    )

    if len(start_times):
        figure.add_trace(
            go.Scatter(
                x=start_times,
                y=np.asarray(signal.values, dtype=float)[start_indices],
                mode="markers",
                marker={"symbol": "star", "size": 10, "color": "rgba(255, 0, 0, 1)"},
                name="Start Indices",
            )
        )

    if len(middle_times):
        figure.add_trace(
            go.Scatter(
                x=middle_times,
                y=np.asarray(signal.values, dtype=float)[middle_indices],
                mode="markers",
                marker={"symbol": "circle", "color": "rgba(0, 255, 0, 1)"},
                name="Middle Indices",
            )
        )

    if len(end_times):
        figure.add_trace(
            go.Scatter(
                x=end_times,
                y=np.asarray(signal.values, dtype=float)[end_indices],
                mode="markers",
                marker={"symbol": "x", "size": 7, "color": "rgba(0, 255, 255, 1)"},
                name="End Indices",
            )
        )

    if tiv_x:
        figure.add_trace(
            go.Scatter(
                x=tiv_x,
                y=tiv_y,
                mode="lines",
                name="TIV",
            )
        )

    figure.update_layout(
        title="Continuous tidal impedance variation",
        xaxis={"title": signal_time_context.axis_title},
        yaxis={"title": f"{signal.category} ({signal.unit})" if signal.unit else signal.category},
        showlegend=True,
    )
    return apply_figure_theme(figure)


def _build_tiv_card(sequence, dataset_start_time: float, selection_start_time: float) -> dict[str, Any] | None:
    signal = _select_signal(sequence)
    if signal is None:
        return None

    tiv_data = TIV().compute_continuous_parameter(signal, store=False)
    tiv_values = np.asarray(tiv_data.values, dtype=float)

    return {
        'title': 'TIV',
        'tables': [
            _serialize_rows(
                [
                    ('Name', tiv_data.name),
                    ('Category', tiv_data.category),
                    ('Unit', tiv_data.unit),
                    ('Events', len(tiv_data)),
                ],
            ),
        ],
        'figures': [
            {
                'role': 'plot',
                'figure': _serialize_figure(
                    _build_continuous_tiv_reference_figure(
                        sequence,
                        dataset_start_time,
                        selection_start_time,
                    ),
                ),
            },
        ],
    }


def _select_active_period(record: SessionRecord, period_options: list[dict[str, int | str]]) -> int | None:
    option_values = {int(option['value']) for option in period_options}
    if record.selected_analyze_period_index in option_values:
        return record.selected_analyze_period_index
    if not period_options:
        record.selected_analyze_period_index = None
        return None

    selected_period = int(period_options[0]['value'])
    record.selected_analyze_period_index = selected_period
    return selected_period


def _get_period(periods: list[SessionStablePeriod], period_index: int) -> SessionStablePeriod:
    for period in periods:
        if period.period_index == period_index:
            return period
    msg = f'Period with index {period_index} not found'
    raise ValueError(msg)


def _should_hide_sparse_artifact(label: str) -> bool:
    return label.lower() in _HIDDEN_SPARSE_LABELS
