import numpy as np
import pytest

from eit_dash.utils.output_rendering import _build_map_animation_figure


def test_build_map_animation_figure_places_controls_next_to_timeline():
    figure = _build_map_animation_figure(
        np.arange(4 * 8 * 8, dtype=float).reshape(4, 8, 8),
        np.array([0.0, 1.0, 2.0, 3.0]),
        "Frame playback",
    )

    slider = figure.layout.sliders[0]

    assert figure.layout.title.text == "Frame playback  |  0.00 s"
    assert slider.active == 0
    assert slider.x == pytest.approx(0.08)
    assert slider.len == pytest.approx(0.8)
    assert slider.y == pytest.approx(-0.15)
    assert [step.label for step in slider.steps] == ["0.0", "1.0", "2.0", "3.0"]
    assert [frame.layout.title.text for frame in figure.frames] == [
        "Frame playback  |  0.00 s",
        "Frame playback  |  1.00 s",
        "Frame playback  |  2.00 s",
        "Frame playback  |  3.00 s",
    ]
    assert len(figure.layout.shapes or []) == 0
    assert len(figure.layout.updatemenus or []) == 0
