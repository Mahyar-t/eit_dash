from unittest.mock import patch

import numpy as np
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from eitprocessing.datahandling.continuousdata import ContinuousData
from eitprocessing.datahandling.sequence import Sequence

import eit_dash.definitions.element_ids as ids
import eit_dash.definitions.layout_styles as styles
from eit_dash.callbacks.preprocessing_callbacks import (
    apply_filter,
    initialize_figure,
    open_periods_modal,
    open_synch_modal,
    select_signals,
    show_filtered_results,
)
from eit_dash.definitions.constants import FILTERED_EIT_LABEL, RAW_EIT_LABEL
from eit_dash.definitions.option_lists import FilterTypes
from eit_dash.utils.data_singleton import LoadedData


@pytest.fixture
def mock_data_object(file_data: Sequence):
    """Mocked object to save and retrieve the data."""
    data_object = LoadedData()
    data_object.add_sequence(file_data)
    data_object.add_stable_period(file_data, 0, 0)

    return data_object


@pytest.fixture
def mock_tmp_results():
    """Mocked temporary results object."""
    return LoadedData()


def test_apply_filter_callback(
    mock_data_object: LoadedData,
    mock_tmp_results: LoadedData,
):
    """Test the filtering of stable periods."""
    low_cut = 1
    high_cut = 9
    filter_order = 1

    with patch(
        "eit_dash.callbacks.preprocessing_callbacks.data_object",
        new=mock_data_object,
    ), patch(
        "eit_dash.callbacks.preprocessing_callbacks.tmp_results",
        new=mock_tmp_results,
    ):
        # test error in filter
        with pytest.raises(TypeError):
            _ = apply_filter(
                0,
                co_low=low_cut,
                co_high=high_cut,
                order=filter_order,
                filter_selected=FilterTypes.lowpass.value,
                results=[],
            )

        # test valid filter
        _ = apply_filter(
            0,
            co_low=low_cut,
            co_high=high_cut,
            order=filter_order,
            filter_selected=FilterTypes.bandpass.value,
            results=[],
        )

        # the filtered results are saved in a temporary object before saving them
        # through a different call. We need to verify if the presence of the data
        # in the mocked temporary object.
        assert "global_impedance_(filtered)" in mock_tmp_results.get_stable_period(0).get_data().continuous_data


def test_initialize_figure_keeps_absolute_overlay_time(file_data: Sequence):
    """Previously selected periods should keep dataset timestamps in preprocessing plots."""
    period = file_data.select_by_time(
        start_time=file_data.time[100],
        end_time=file_data.time[110],
    )

    loaded_data = LoadedData()
    loaded_data.add_sequence(file_data)
    loaded_data.add_stable_period(period, 0, 0)

    with patch("eit_dash.callbacks.preprocessing_callbacks.data_object", new=loaded_data), patch(
        "eit_dash.callbacks.preprocessing_callbacks.time.sleep",
        return_value=None,
    ):
        figure, _, _ = initialize_figure("0")

    overlay_trace = next(trace for trace in figure.data if trace.meta and trace.meta["uid"] == 0 and trace.name == RAW_EIT_LABEL)

    assert figure.data[0].x[0] == pytest.approx(file_data.time[0])
    assert overlay_trace.x[0] == pytest.approx(period.continuous_data[RAW_EIT_LABEL].time[0])
    assert overlay_trace.customdata[0][0] == pytest.approx(period.continuous_data[RAW_EIT_LABEL].time[0] - file_data.time[0])
    assert overlay_trace.customdata[0][1] == pytest.approx(0.0)
    assert "Elapsed from period start" in overlay_trace.hovertemplate


def test_select_signals_hides_unused_y_axes(file_data: Sequence):
    """Only the checked signal axes should remain visible in period selection."""
    loaded_data = LoadedData()
    loaded_data.add_sequence(file_data)

    with patch("eit_dash.callbacks.preprocessing_callbacks.data_object", new=loaded_data), patch(
        "eit_dash.callbacks.preprocessing_callbacks.time.sleep",
        return_value=None,
    ):
        figure, _, checkbox_row = initialize_figure("0")

    checklist = checkbox_row[1]
    options = checklist.options
    raw_index = next(index for index, option in enumerate(options) if option["label"] == RAW_EIT_LABEL)

    updated_figure, _ = select_signals([raw_index], options, figure.to_plotly_json())

    assert updated_figure["layout"]["yaxis"]["visible"] is True
    for axis_name, axis in updated_figure["layout"].items():
        if str(axis_name).startswith("yaxis") and axis_name != "yaxis":
            assert axis["visible"] is False


def test_show_filtered_results_keeps_absolute_period_time(file_data: Sequence):
    """Filtering results should use dataset time on the x-axis and period-relative hover metadata."""
    period = file_data.select_by_time(
        start_time=file_data.time[100],
        end_time=file_data.time[110],
    )
    filtered_period = file_data.select_by_time(
        start_time=file_data.time[100],
        end_time=file_data.time[110],
    )

    if FILTERED_EIT_LABEL in period.continuous_data:
        period.continuous_data.pop(FILTERED_EIT_LABEL)
    if FILTERED_EIT_LABEL in filtered_period.continuous_data:
        filtered_period.continuous_data.pop(FILTERED_EIT_LABEL)

    raw_signal = filtered_period.continuous_data[RAW_EIT_LABEL]
    filtered_period.continuous_data.add(
        ContinuousData(
            label=FILTERED_EIT_LABEL,
            name="Filtered global impedance",
            unit=raw_signal.unit,
            category=raw_signal.category,
            time=np.copy(raw_signal.time),
            values=np.copy(raw_signal.values) + 1.0,
            sample_frequency=raw_signal.sample_frequency,
        ),
    )

    loaded_data = LoadedData()
    loaded_data.add_sequence(file_data)
    loaded_data.add_stable_period(period, 0, 0)

    tmp_results = LoadedData()
    tmp_results.add_stable_period(filtered_period, 0, 0)

    with patch("eit_dash.callbacks.preprocessing_callbacks.data_object", new=loaded_data), patch(
        "eit_dash.callbacks.preprocessing_callbacks.tmp_results",
        new=tmp_results,
    ):
        figure, style = show_filtered_results(None, "updated", "0")

    assert style == styles.GRAPH
    assert figure.data[0].x[0] == pytest.approx(period.continuous_data[RAW_EIT_LABEL].time[0])
    assert figure.data[1].x[0] == pytest.approx(filtered_period.continuous_data[FILTERED_EIT_LABEL].time[0])
    assert figure.data[0].customdata[0][0] == pytest.approx(period.continuous_data[RAW_EIT_LABEL].time[0] - file_data.time[0])
    assert figure.data[0].customdata[0][1] == pytest.approx(0.0)
    assert "Elapsed from period start" in figure.data[0].hovertemplate
    assert figure.layout.xaxis.title.text == "Dataset time (ms)"


def test_open_synch_modal_callback():
    """Test opening of synchronization modal."""
    context_value.set(
        AttributeDict(
            triggered_inputs=[{"prop_id": f"{ids.OPEN_SYNCH_BUTTON}.n_clicks"}],
        ),
    )

    output = open_synch_modal(1, 1)

    expected_output = True

    # verify that a different input produces a different output
    context_value.set(
        AttributeDict(
            triggered_inputs=[
                {"prop_id": f"{ids.SYNCHRONIZATION_CONFIRM_BUTTON}.n_clicks"},
            ],
        ),
    )

    output_new_params = open_synch_modal(1, 1)

    assert output == expected_output
    assert output_new_params != expected_output


def test_open_periods_modal_callback():
    """Test opening of the modal for selecting the stable periods."""
    context_value.set(
        AttributeDict(
            triggered_inputs=[
                {"prop_id": f"{ids.OPEN_SELECT_PERIODS_BUTTON}.n_clicks"},
            ],
        ),
    )

    output = open_periods_modal(1, 1)

    expected_output = True

    # verify that a different input produces a different output
    context_value.set(
        AttributeDict(
            triggered_inputs=[{"prop_id": f"{ids.PERIODS_CONFIRM_BUTTON}.n_clicks"}],
        ),
    )

    output_new_params = open_periods_modal(1, 1)

    assert output == expected_output
    assert output_new_params != expected_output
