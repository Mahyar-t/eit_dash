from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TimeAxisContext:
    """Shared x-axis metadata for plots that should retain dataset timestamps."""

    x: np.ndarray
    customdata: np.ndarray
    axis_title: str
    hovertemplate: str


def build_time_axis_context(
    time,
    *,
    dataset_start_time: float,
    selection_start_time: float | None = None,
    y_suffix: str = "<extra></extra>",
) -> TimeAxisContext:
    """Build x-axis and hover metadata without rebasing the original timestamps."""
    time_array = np.asarray(time, dtype=float)
    selection_start = dataset_start_time if selection_start_time is None else selection_start_time

    customdata = np.column_stack(
        (
            time_array - float(dataset_start_time),
            time_array - float(selection_start),
        ),
    )

    hover_lines = [
        "Dataset time: %{x:.3f} s",
        "Elapsed from dataset start: %{customdata[0]:.3f} s",
    ]
    if not np.isclose(selection_start, dataset_start_time):
        hover_lines.append("Elapsed from period start: %{customdata[1]:.3f} s")

    return TimeAxisContext(
        x=time_array,
        customdata=customdata,
        axis_title="Dataset time (s)",
        hovertemplate="<br>".join(hover_lines) + y_suffix,
    )
