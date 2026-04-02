from __future__ import annotations

import contextlib
import json
from typing import Any

import numpy as np
from eitprocessing.parameters.eeli import EELI

from backend.services.load_service import serialize_dataset
from backend.services.preprocessing_service import _serialize_filter_card, _serialize_period_card
from backend.state.session_store import SessionRecord, SessionStablePeriod
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
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


_ANALYZE_SPARSE_LABEL = 'continuous_eelis'


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
        'title': f'Continuous Data ({len(sequence.continuous_data)})',
        'items': items,
        'empty_message': 'No continuous outputs available for this period.' if not items else None,
    }


def _serialize_sparse_section(sequence, dataset_start_time: float, selection_start_time: float) -> dict[str, Any]:
    items = []

    for label, data in _collection_items(sequence.sparse_data):
        card = {
            'title': label,
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
                        _build_sparse_numeric_figure(data, dataset_start_time, selection_start_time),
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

    return {
        'title': f'Sparse Data ({len(sequence.sparse_data)})',
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
