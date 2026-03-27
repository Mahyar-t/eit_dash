from __future__ import annotations

from typing import TYPE_CHECKING, Any

import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from eitprocessing.datahandling.breath import Breath
from eitprocessing.datahandling.continuousdata import ContinuousData
from eitprocessing.datahandling.eitdata import EITData
from eitprocessing.datahandling.intervaldata import IntervalData
from eitprocessing.datahandling.sparsedata import SparseData

from eit_dash.definitions import element_ids as ids
from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.utils.common import apply_figure_theme
from eit_dash.utils.time_axis import build_time_axis_context

if TYPE_CHECKING:
    from eitprocessing.datahandling.sequence import Sequence


_MAX_TABLE_ROWS = 12
_MAX_ANIMATION_FRAMES = 90
_MAP_GRAPH_CONFIG = {"modeBarButtonsToRemove": ["zoom2d", "select2d", "lasso2d"]}

_FRAME_DURATION_MS = 80  # animation frame duration in milliseconds


def render_sequence_outputs(
    sequence: Sequence, source_dataset: Sequence | None = None, period_index: int | None = None
) -> list:
    """Render all output collections stored in a Sequence."""
    dataset_start_time = _get_dataset_start_time(sequence, source_dataset)
    selection_start_time = _get_selection_start_time(sequence)

    return [
        _render_overview_card(sequence),
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    _render_eit_collection(sequence, dataset_start_time, selection_start_time, period_index),
                    title=f"EIT Data ({len(sequence.eit_data)})",
                ),
                dbc.AccordionItem(
                    _render_continuous_collection(sequence, dataset_start_time, selection_start_time),
                    title=f"Continuous Data ({len(sequence.continuous_data)})",
                ),
                dbc.AccordionItem(
                    _render_sparse_collection(sequence, dataset_start_time, selection_start_time),
                    title=f"Sparse Data ({len(sequence.sparse_data)})",
                ),
                dbc.AccordionItem(
                    _render_interval_collection(sequence),
                    title=f"Interval Data ({len(sequence.interval_data)})",
                ),
            ],
            always_open=True,
            start_collapsed=False,
            className="mt-3",
        ),
    ]


def _get_dataset_start_time(sequence: Sequence, source_dataset: Sequence | None) -> float:
    if source_dataset is not None:
        if RAW_EIT_LABEL in source_dataset.continuous_data:
            return float(source_dataset.continuous_data[RAW_EIT_LABEL].time[0])
        return float(source_dataset.eit_data["raw"].time[0])

    if RAW_EIT_LABEL in sequence.continuous_data:
        return float(sequence.continuous_data[RAW_EIT_LABEL].time[0])
    return float(sequence.eit_data["raw"].time[0])


def _get_selection_start_time(sequence: Sequence) -> float:
    if RAW_EIT_LABEL in sequence.continuous_data:
        return float(sequence.continuous_data[RAW_EIT_LABEL].time[0])
    if len(sequence.eit_data):
        return float(sequence.eit_data["raw"].time[0])
    if len(sequence.sparse_data):
        first_sparse = next(iter(sequence.sparse_data.values()))
        return float(first_sparse.time[0])
    if len(sequence.interval_data):
        first_interval = next(iter(sequence.interval_data.values()))
        return float(first_interval.intervals[0].start_time)
    return 0.0


def _render_overview_card(sequence: Sequence) -> dbc.Card:
    rows = [
        ("Sequence", sequence.label),
        ("EIT collections", len(sequence.eit_data)),
        ("Continuous collections", len(sequence.continuous_data)),
        ("Sparse collections", len(sequence.sparse_data)),
        ("Interval collections", len(sequence.interval_data)),
    ]
    return _make_card("Output Overview", [_make_table(rows)])


def _render_eit_collection(
    sequence: Sequence,
    dataset_start_time: float,
    selection_start_time: float,
    period_index: int | None,
) -> list:
    if not len(sequence.eit_data):
        return [dbc.Alert("No EIT outputs available for this period.", color="secondary", className="mb-0")]

    return [
        _make_card(
            label,
            [
                _make_table(
                    [
                        ("Vendor", getattr(eit_data.vendor, "value", str(eit_data.vendor))),
                        ("Frames", eit_data.nframes),
                        ("Shape", eit_data.pixel_impedance.shape),
                        ("Sample frequency", f"{eit_data.sample_frequency:.3f} Hz"),
                        ("Start time", f"{eit_data.time[0]:.3f} s"),
                        ("End time", f"{eit_data.time[-1]:.3f} s"),
                        ("Path", eit_data.path),
                    ],
                ),
                dcc.Graph(figure=_build_eit_signal_figure(eit_data, dataset_start_time, selection_start_time)),
                dcc.Graph(
                    id=_eit_frame_graph_id(period_index, label),
                    figure=_build_map_animation_figure(eit_data.pixel_impedance, eit_data.time, "Frame playback"),
                    config=_MAP_GRAPH_CONFIG,
                    style={"height": "800px"},
                ),
                _build_playback_controls(period_index, label),
                _build_frame_count_control(eit_data, period_index),
            ],
        )
        for label, eit_data in _collection_items(sequence.eit_data)
    ]


def _render_continuous_collection(sequence: Sequence, dataset_start_time: float, selection_start_time: float) -> list:
    if not len(sequence.continuous_data):
        return [dbc.Alert("No continuous outputs available for this period.", color="secondary", className="mb-0")]

    return [
        _make_card(
            label,
            [
                _make_table(
                    [
                        ("Name", data.name),
                        ("Category", data.category),
                        ("Unit", data.unit),
                        ("Samples", len(data)),
                        (
                            "Sample frequency",
                            f"{data.sample_frequency:.3f} Hz" if data.sample_frequency is not None else "n/a",
                        ),
                        ("Start time", f"{data.time[0]:.3f} s"),
                        ("End time", f"{data.time[-1]:.3f} s"),
                    ],
                ),
                dcc.Graph(figure=_build_continuous_figure(data, dataset_start_time, selection_start_time)),
            ],
        )
        for label, data in _collection_items(sequence.continuous_data)
    ]


def _render_sparse_collection(sequence: Sequence, dataset_start_time: float, selection_start_time: float) -> list:
    if not len(sequence.sparse_data):
        return [dbc.Alert("No sparse outputs available for this period.", color="secondary", className="mb-0")]

    rendered = []
    for label, data in _collection_items(sequence.sparse_data):
        children = [
            _make_table(
                [
                    ("Name", data.name),
                    ("Category", data.category),
                    ("Unit", data.unit),
                    ("Events", len(data)),
                ],
            ),
        ]

        if not data.has_values:
            children.append(_make_table(_sparse_rows_without_values(data)))
        elif _values_are_numeric_scalars(data.values):
            children.append(dcc.Graph(figure=_build_sparse_numeric_figure(data, dataset_start_time, selection_start_time)))
            children.append(_make_table(_numeric_summary_rows(np.asarray(data.values, dtype=float))))
        elif _values_are_2d_maps(data.values):
            children.append(
                dcc.Graph(
                    figure=_build_map_animation_figure(np.asarray(data.values), data.time, "Map playback"),
                    config=_MAP_GRAPH_CONFIG,
                )
            )
            children.append(_make_table(_sparse_preview_rows(data)))
        else:
            children.append(_make_table(_sparse_preview_rows(data)))

        rendered.append(_make_card(label, children))

    return rendered


def _render_interval_collection(sequence: Sequence) -> list:
    if not len(sequence.interval_data):
        return [dbc.Alert("No interval outputs available for this period.", color="secondary", className="mb-0")]

    rendered = []
    for label, data in _collection_items(sequence.interval_data):
        children = [
            _make_table(
                [
                    ("Name", data.name),
                    ("Category", data.category),
                    ("Unit", data.unit),
                    ("Intervals", len(data)),
                ],
            ),
            _make_table(_interval_rows(data)),
        ]
        rendered.append(_make_card(label, children))
    return rendered


def _build_eit_signal_figure(eit_data: EITData, dataset_start_time: float, selection_start_time: float) -> go.Figure:
    summed_impedance = np.nansum(eit_data.pixel_impedance, axis=(1, 2))
    time_context = build_time_axis_context(
        eit_data.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Summed impedance: %{y:.3f}<extra></extra>",
    )

    figure = go.Figure(
        go.Scatter(
            x=time_context.x,
            y=summed_impedance,
            customdata=time_context.customdata,
            hovertemplate=time_context.hovertemplate,
            name="Summed impedance",
            line={"color": "#38bdf8", "width": 2},
        )
    )
    figure.update_layout(
        title="Summed impedance over time",
        xaxis={"title": time_context.axis_title},
        yaxis={"title": "Summed impedance (a.u.)"},
        showlegend=False,
    )
    return apply_figure_theme(figure)


def _build_continuous_figure(
    data: ContinuousData, dataset_start_time: float, selection_start_time: float
) -> go.Figure:
    time_context = build_time_axis_context(
        data.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Value: %{y:.3f}<extra></extra>",
    )
    figure = go.Figure(
        go.Scatter(
            x=time_context.x,
            y=data.values,
            customdata=time_context.customdata,
            hovertemplate=time_context.hovertemplate,
            name=data.label,
            line={"color": "#22c55e", "width": 2},
        )
    )
    figure.update_layout(
        title=data.name,
        xaxis={"title": time_context.axis_title},
        yaxis={"title": f"{data.category} ({data.unit})" if data.unit else data.category},
        showlegend=False,
    )
    return apply_figure_theme(figure)


def _build_sparse_numeric_figure(
    data: SparseData, dataset_start_time: float, selection_start_time: float
) -> go.Figure:
    values = np.asarray(data.values, dtype=float)
    time_context = build_time_axis_context(
        data.time,
        dataset_start_time=dataset_start_time,
        selection_start_time=selection_start_time,
        y_suffix="<br>Value: %{y:.3f}<extra></extra>",
    )
    figure = go.Figure(
        go.Scatter(
            x=time_context.x,
            y=values,
            customdata=time_context.customdata,
            hovertemplate=time_context.hovertemplate,
            mode="lines+markers",
            line={"color": "#ef4444", "width": 2},
            marker={"size": 8, "color": "#ef4444"},
            name=data.label,
        )
    )
    figure.update_layout(
        title=data.name,
        xaxis={"title": time_context.axis_title},
        yaxis={"title": f"{data.category} ({data.unit})" if data.unit else data.category},
        showlegend=False,
    )
    return apply_figure_theme(figure)


def _build_map_animation_figure(values: np.ndarray, time_values, title: str, max_frames: int | None = None) -> go.Figure:
    """Build an animated heatmap figure with Plotly's native slider scrubber.

    Time is shown live in the figure title (updated per frame), so no
    separate progress-bar overlay or currentvalue label is needed.
    Play/Pause/Reset are handled by external Dash buttons (see _build_playback_controls).
    """
    indices = _animation_indices(len(values), max_frames=max_frames)
    displayed_values = np.asarray(values[indices], dtype=float)
    displayed_time = np.asarray(time_values, dtype=float)[indices]

    has_values = np.any(~np.isnan(displayed_values))
    zmin = float(np.nanmin(displayed_values)) if has_values else None
    zmax = float(np.nanmax(displayed_values)) if has_values else None

    _heatmap_kwargs = dict(
        colorscale="Viridis",
        zmin=zmin,
        zmax=zmax,
        hovertemplate="Row %{y}<br>Col %{x}<br>Value %{z:.3f}<extra></extra>",
    )

    frame_names = [f"frame-{i}" for i in range(len(displayed_values))]
    sample_note = f" — sampled {len(indices)} of {len(values)} frames" if len(indices) < len(values) else ""

    def _frame_title(t: float) -> str:
        return f"{title}{sample_note}  |  {t:.2f} s"

    plot_domain = [0.08, 0.88]
    colorbar_x = 0.93

    figure = go.Figure(
        data=[
            go.Heatmap(
                z=np.asarray(displayed_values[0], dtype=float),
                colorbar={"title": "Value", "x": colorbar_x, "len": 0.9},
                **_heatmap_kwargs,
            )
        ],
        frames=[
            go.Frame(
                data=[go.Heatmap(z=np.asarray(frame_values, dtype=float), **_heatmap_kwargs)],
                layout=go.Layout(title=_frame_title(t)),
                name=frame_name,
            )
            for frame_name, frame_values, t in zip(frame_names, displayed_values, displayed_time, strict=True)
        ],
    )

    # One slider step per frame; clicking a step jumps directly to that frame.
    slider_steps = [
        {
            "args": [
                [frame_name],
                {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}},
            ],
            "label": f"{t:.1f}",
            "method": "animate",
        }
        for frame_name, t in zip(frame_names, displayed_time, strict=True)
    ]

    figure = apply_figure_theme(figure)
    figure.update_layout(
        title=_frame_title(displayed_time[0]),
        xaxis={"showticklabels": False, "constrain": "domain", "domain": plot_domain},
        yaxis={"showticklabels": False, "scaleanchor": "x", "scaleratio": 1, "constrain": "domain"},
        margin={"t": 60, "l": 20, "b": 60, "r": 20},
        sliders=[
            {
                "active": 0,
                "steps": slider_steps,
                "x": plot_domain[0],
                "len": plot_domain[1] - plot_domain[0],
                "xanchor": "left",
                "y": -0.15,
                "yanchor": "top",
                "pad": {"t": 18, "b": 0, "l": 0, "r": 0},
                "currentvalue": {"visible": False},
                "transition": {"duration": 0},
                "bgcolor": "rgba(56, 189, 248, 0.55)",
                "bordercolor": "rgba(148, 163, 184, 0.35)",
                "tickcolor": "rgba(148, 163, 184, 0.4)",
                "font": {"color": "rgba(148, 163, 184, 0.75)", "size": 10},
                "minorticklen": 0,
            }
        ],
    )
    return figure


def _playback_btn_id(id_type: str, period_index: int | None, label: str) -> dict:
    return {"type": id_type, "period": period_index, "label": label}


def _build_playback_controls(period_index: int | None, label: str) -> html.Div:
    """External Dash control row: Play/Pause toggle + Reset button + hidden state store."""
    return html.Div(
        [
            dcc.Store(id=_playback_btn_id(ids.ANALYZE_EIT_PLAY_STATE, period_index, label), data=False),
            dbc.Button(
                "\u25b6\ufe0f Play",
                id=_playback_btn_id(ids.ANALYZE_EIT_PLAY_BTN, period_index, label),
                color="primary",
                size="sm",
                outline=True,
                className="me-2 playback-btn",
            ),
            dbc.Button(
                "\u23ee\ufe0f Reset",
                id=_playback_btn_id(ids.ANALYZE_EIT_RESET_BTN, period_index, label),
                color="secondary",
                size="sm",
                outline=True,
                className="playback-btn",
            ),
        ],
        className="d-flex align-items-center mt-2 mb-1",
    )



def _animation_indices(length: int, max_frames: int | None = None) -> np.ndarray:
    frame_limit = _coerce_animation_frame_count(max_frames, length)
    if length <= frame_limit:
        return np.arange(length, dtype=int)
    return np.unique(np.linspace(0, length - 1, num=frame_limit, dtype=int))


def _coerce_animation_frame_count(requested_frames: int | None, available_frames: int) -> int:
    if available_frames <= 0:
        return 0
    if requested_frames is None:
        return min(_MAX_ANIMATION_FRAMES, available_frames)
    return max(1, min(int(requested_frames), available_frames))


def _default_animation_frame_count(available_frames: int) -> int:
    return _coerce_animation_frame_count(_MAX_ANIMATION_FRAMES, available_frames)


def _eit_frame_graph_id(period_index: int | None, label: str) -> dict[str, str | int | None]:
    return {"type": ids.ANALYZE_EIT_FRAME_GRAPH, "period": period_index, "label": label}


def _eit_frame_count_input_id(period_index: int | None, label: str) -> dict[str, str | int | None]:
    return {"type": ids.ANALYZE_EIT_FRAME_COUNT_INPUT, "period": period_index, "label": label}


def _build_frame_count_control(eit_data: EITData, period_index: int | None) -> dbc.Row:
    frame_count = _default_animation_frame_count(eit_data.nframes)
    return dbc.Row(
        [
            dbc.Col(
                html.Div("Frames to show", className="small text-uppercase text-muted"),
                width="auto",
                className="pe-0",
            ),
            dbc.Col(
                dbc.Input(
                    id=_eit_frame_count_input_id(period_index, eit_data.label),
                    type="number",
                    min=1,
                    max=eit_data.nframes,
                    step=1,
                    value=frame_count,
                    size="sm",
                    style={
                        "height": "30px",
                        "padding": "0.2rem 0.5rem",
                        "fontSize": "0.875rem",
                        "lineHeight": "1.2",
                    },
                ),
                width="auto",
            ),
        ],
        className="g-2 align-items-center mt-2",
        justify="start",
    )



def _numeric_summary_rows(values: np.ndarray) -> list[tuple[str, str]]:
    if values.size == 0:
        return [("Values", "No numeric values")]
    return [
        ("Mean", f"{np.nanmean(values):.3f}"),
        ("Median", f"{np.nanmedian(values):.3f}"),
        ("Standard deviation", f"{np.nanstd(values):.3f}"),
        ("Minimum", f"{np.nanmin(values):.3f}"),
        ("Maximum", f"{np.nanmax(values):.3f}"),
    ]


def _sparse_rows_without_values(data: SparseData) -> list[tuple[str, str]]:
    rows = [("Time", f"{time_value:.3f} s") for time_value in np.asarray(data.time[:_MAX_TABLE_ROWS], dtype=float)]
    if len(data) > _MAX_TABLE_ROWS:
        rows.append(("...", f"{len(data) - _MAX_TABLE_ROWS} more event(s)"))
    return rows


def _sparse_preview_rows(data: SparseData) -> list[tuple[str, str]]:
    rows = []
    preview_count = min(len(data), _MAX_TABLE_ROWS)
    for index in range(preview_count):
        rows.append((f"{float(data.time[index]):.3f} s", _summarize_value(data.values[index])))
    if len(data) > _MAX_TABLE_ROWS:
        rows.append(("...", f"{len(data) - _MAX_TABLE_ROWS} more event(s)"))
    return rows


def _interval_rows(data: IntervalData) -> list[tuple[str, str]]:
    rows = []
    preview_count = min(len(data), _MAX_TABLE_ROWS)
    for index in range(preview_count):
        interval = data.intervals[index]
        row_label = f"{interval.start_time:.3f} - {interval.end_time:.3f} s"
        value = data.values[index] if data.has_values else None
        if isinstance(value, Breath):
            row_value = f"Breath(start={value.start_time:.3f}, middle={value.middle_time:.3f}, end={value.end_time:.3f})"
        else:
            row_value = _summarize_value(value) if data.has_values else "Interval"
        rows.append((row_label, row_value))
    if len(data) > _MAX_TABLE_ROWS:
        rows.append(("...", f"{len(data) - _MAX_TABLE_ROWS} more interval(s)"))
    return rows


def _values_are_numeric_scalars(values: Any) -> bool:
    try:
        return all(np.isscalar(value) and np.isreal(value) for value in values)
    except TypeError:
        return False


def _values_are_2d_maps(values: Any) -> bool:
    try:
        arrays = [np.asarray(value, dtype=float) for value in values]
    except (TypeError, ValueError):
        return False
    return bool(arrays) and all(array.ndim == 2 for array in arrays)


def _summarize_value(value: Any) -> str:
    if value is None:
        return "None"
    if isinstance(value, Breath):
        return f"Breath({value.start_time:.3f}, {value.middle_time:.3f}, {value.end_time:.3f})"
    if isinstance(value, np.ndarray):
        return f"array(shape={value.shape}, min={np.nanmin(value):.3f}, max={np.nanmax(value):.3f})"
    return str(value)


def _collection_items(collection) -> list[tuple[str, Any]]:
    return [(label, collection[label]) for label in collection]


def _make_card(title: str, children: list) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([html.H4(title, className="card-title"), *children]),
        className="glass-card mb-3",
    )


def _make_table(rows: list[tuple[str, Any]]) -> html.Table:
    return html.Table(
        [
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Td(label, className="info-table__label"),
                            html.Td(str(value), className="info-table__value"),
                        ]
                    )
                    for label, value in rows
                ]
            )
        ],
        className="info-table mb-3",
    )
