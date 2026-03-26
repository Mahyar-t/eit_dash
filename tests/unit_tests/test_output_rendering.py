import numpy as np
import pytest

from eit_dash.utils.output_rendering import _build_map_animation_figure


def test_build_map_animation_figure_places_controls_next_to_timeline():
    figure = _build_map_animation_figure(
        np.arange(4 * 8 * 8, dtype=float).reshape(4, 8, 8),
        np.array([0.0, 1000.0, 2000.0, 3000.0]),
        "Frame playback",
    )

    track = figure.layout.shapes[0]
    buttons = figure.layout.updatemenus[0]
    annotations = {annotation.text: annotation for annotation in figure.layout.annotations}

    assert track.x0 == pytest.approx(0.12)
    assert track.x1 == pytest.approx(0.82)
    assert buttons.x < track.x0
    assert buttons.direction == "down"
    assert buttons.xanchor == "left"
    assert buttons.yanchor == "top"
    assert buttons.y == pytest.approx(track.y1)
    assert annotations["0.00 s"].y < track.y0
    assert annotations["0.00 s"].y > annotations["Time (s)"].y
    assert annotations["0.00"].x == pytest.approx(track.x0)
    assert annotations["3.00"].x == pytest.approx(track.x1)
