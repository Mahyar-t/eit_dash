import numpy as np

from eit_dash.utils.time_axis import build_time_axis_context


def test_build_time_axis_context_for_period_slice():
    time = np.array([10.0, 10.02, 10.04])

    context = build_time_axis_context(
        time,
        dataset_start_time=0.0,
        selection_start_time=10.0,
    )

    np.testing.assert_allclose(context.x, time)
    np.testing.assert_allclose(context.customdata[:, 0], [10.0, 10.02, 10.04])
    np.testing.assert_allclose(context.customdata[:, 1], [0.0, 0.02, 0.04])
    assert "Elapsed from period start" in context.hovertemplate


def test_build_time_axis_context_for_full_dataset():
    time = np.array([0.0, 0.02, 0.04])

    context = build_time_axis_context(
        time,
        dataset_start_time=0.0,
    )

    np.testing.assert_allclose(context.x, time)
    np.testing.assert_allclose(context.customdata[:, 0], [0.0, 0.02, 0.04])
    np.testing.assert_allclose(context.customdata[:, 1], [0.0, 0.02, 0.04])
    assert "Elapsed from period start" not in context.hovertemplate


def test_build_time_axis_context_for_non_zero_dataset_start():
    time = np.array([46909.971, 46910.021])

    context = build_time_axis_context(
        time,
        dataset_start_time=46905.221,
        selection_start_time=46909.971,
    )

    np.testing.assert_allclose(context.x, time)
    np.testing.assert_allclose(context.customdata[:, 0], [4.75, 4.8])
    np.testing.assert_allclose(context.customdata[:, 1], [0.0, 0.05])
