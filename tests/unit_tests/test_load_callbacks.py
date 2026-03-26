from unittest.mock import patch

import pytest
import plotly.graph_objects as go
from dash._callback_context import context_value
from dash._utils import AttributeDict
from eitprocessing.datahandling.eitdata import Vendor
from eitprocessing.datahandling.sequence import Sequence

import eit_dash.definitions.element_ids as ids
from eit_dash.callbacks.load_callbacks import get_signal_options, load_selected_data, show_info
from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.definitions.option_lists import InputFiletypes
from tests.conftest import data_path

FIRST_SAMPLE = 100
LAST_SAMPLE = 1000

CUT_FILE_LENGTH = LAST_SAMPLE - FIRST_SAMPLE


@pytest.fixture(scope="session")
def expected_cut_info_data(file_data: Sequence):
    """This is fixture that returns the expected structure for the information contained in the loaded file."""
    return {
        "Name": data_path.name,
        "n_frames": CUT_FILE_LENGTH,
        "start_time": file_data.time[FIRST_SAMPLE],
        "end_time": file_data.time[LAST_SAMPLE - 1],
        "vendor": Vendor.DRAEGER,
        "continuous signals": [RAW_EIT_LABEL],
        "path": str(data_path),
    }


def test_load_selected_data_callback(file_data: Sequence, expected_cut_info_data: dict):
    """Test the loading of data from a selected file."""
    cancel_load = 0
    sig = []
    file_type = InputFiletypes.Draeger.value
    fig = go.Figure()

    # cancel data button input
    context_value.set(
        AttributeDict(
            triggered_inputs=[{"prop_id": f"{ids.LOAD_CANCEL_BUTTON}.n_clicks"}],
        ),
    )
    output = load_selected_data(data_path, cancel_load, sig, file_type, fig)

    assert output == (True, [], [], go.Figure())

    # file selected input
    context_value.set(
        AttributeDict(
            triggered_inputs=[{"prop_id": f"{ids.NFILES_PLACEHOLDER}.n_clicks"}],
        ),
    )

    # run the callback
    output = load_selected_data(data_path, cancel_load, sig, file_type, fig)

    # the output of this function is a figure that uses the loaded data
    # we can check the data in the figure to verify the correct data loading
    figure = output[3]
    fig_data = figure.data[0]["x"]

    assert len(fig_data) == len(file_data.time)
    assert fig_data[0] == pytest.approx(file_data.time[0])
    assert fig_data[-1] == pytest.approx(file_data.time[-1])
    assert figure.data[0]["customdata"][0][0] == pytest.approx(0.0)
    assert figure.data[0]["customdata"][0][1] == pytest.approx(0.0)
    assert "Elapsed from dataset start" in figure.data[0]["hovertemplate"]
    assert "Elapsed from period start" not in figure.data[0]["hovertemplate"]
    assert figure.layout.xaxis.title.text == "Dataset time (ms)"

    # we can check that also the other continuous data has been detected and displayed as options

    assert output[1] == get_signal_options(file_data)


def test_show_info_callback(file_data: Sequence, expected_cut_info_data: dict):
    """Test the slicing of the data through the periods selection."""
    # run the callback
    with patch("eit_dash.callbacks.load_callbacks.file_data", new=file_data):
        output = show_info(
            btn_click=1,
            loaded_data=data_path,
            container_state=None,
            filetype="1",
            slidebar_stat={
                "xaxis.range": [
                    file_data.time[FIRST_SAMPLE],
                    file_data.time[LAST_SAMPLE],
                ],
            },
            selected_signals=[],
            signals_options=get_signal_options(file_data),
            custom_name=None,
        )

    # the output is a card containing the information about the selected signal.
    # We have to check that the information is the expected one to verify the correct slicing

    assert len(output[0]) == 1
    assert output[1] is True

    card_text = str(output[0][0])
    assert expected_cut_info_data["Name"] in card_text
    assert f"{expected_cut_info_data['start_time']:.3f} ms" in card_text
    assert f"{expected_cut_info_data['end_time']:.3f} ms" in card_text
    assert expected_cut_info_data["vendor"].value in card_text
    assert RAW_EIT_LABEL in card_text
    assert expected_cut_info_data["path"] in card_text
