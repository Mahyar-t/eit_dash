from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from eitprocessing.datahandling.continuousdata import ContinuousData
from eitprocessing.datahandling.datacollection import DataCollection
from eitprocessing.datahandling.eitdata import EITData, Vendor
from eitprocessing.datahandling.sequence import Sequence

from eit_dash.callbacks import analyze_callbacks
from eit_dash.definitions.constants import RAW_EIT_LABEL
from eit_dash.utils.data_singleton import LoadedData


def make_sequence(time_values, *, label: str, vendor: Vendor, sample_frequency: float) -> Sequence:
    time = np.asarray(time_values, dtype=float)
    raw_values = np.arange(len(time), dtype=float)
    eit_data = EITData(
        path=Path(f"{label}.bin"),
        nframes=len(time),
        time=time,
        sample_frequency=sample_frequency,
        vendor=vendor,
        label="raw",
        pixel_impedance=np.zeros((len(time), 32, 32), dtype=float),
    )
    continuous_data = DataCollection(ContinuousData)
    continuous_data.add(
        ContinuousData(
            label=RAW_EIT_LABEL,
            name="Global impedance",
            unit="a.u.",
            category="impedance",
            time=time,
            values=raw_values,
            sample_frequency=sample_frequency,
        ),
    )

    return Sequence(
        label=label,
        eit_data=DataCollection(EITData, raw=eit_data),
        continuous_data=continuous_data,
    )


def test_show_eeli_keeps_absolute_timpel_period_time():
    source = make_sequence(np.arange(0.0, 10.1, 0.02), label="timpel_dataset", vendor=Vendor.TIMPEL, sample_frequency=50.0)
    period = make_sequence([10.0, 10.02, 10.04], label="Period 0", vendor=Vendor.TIMPEL, sample_frequency=50.0)

    loaded_data = LoadedData()
    loaded_data.add_sequence(source)
    loaded_data.add_stable_period(period, 0, 0)

    eeli_results = [
        {
            "index": 0,
            "time": np.array([10.0, 10.04]),
            "values": np.array([1.0, 2.0]),
            "mean": None,
            "median": None,
            "standard deviation": None,
        },
    ]

    with patch.object(analyze_callbacks, "data_object", new=loaded_data), patch.object(
        analyze_callbacks,
        "eeli",
        new=eeli_results,
    ):
        figure, _ = analyze_callbacks.show_eeli(0, 1)

    assert figure.data[0].x[0] == pytest.approx(10.0)
    assert figure.data[1].x[0] == pytest.approx(10.0)
    assert figure.data[0].customdata[0][0] == pytest.approx(10.0)
    assert figure.data[0].customdata[0][1] == pytest.approx(0.0)
    assert "Elapsed from period start" in figure.data[0].hovertemplate
    assert figure.layout.xaxis2.title.text == "Dataset time (s)"


def test_show_eeli_keeps_absolute_draeger_period_time():
    source = make_sequence(
        [46905.221, 46905.271, 46909.971, 46910.021, 46910.071],
        label="draeger_dataset",
        vendor=Vendor.DRAEGER,
        sample_frequency=20.0,
    )
    period = make_sequence(
        [46909.971, 46910.021, 46910.071],
        label="Period 0",
        vendor=Vendor.DRAEGER,
        sample_frequency=20.0,
    )

    loaded_data = LoadedData()
    loaded_data.add_sequence(source)
    loaded_data.add_stable_period(period, 0, 0)

    eeli_results = [
        {
            "index": 0,
            "time": np.array([46909.971, 46910.021]),
            "values": np.array([0.5, 0.8]),
            "mean": None,
            "median": None,
            "standard deviation": None,
        },
    ]

    with patch.object(analyze_callbacks, "data_object", new=loaded_data), patch.object(
        analyze_callbacks,
        "eeli",
        new=eeli_results,
    ):
        figure, _ = analyze_callbacks.show_eeli(0, 1)

    assert figure.data[0].x[0] == pytest.approx(46909.971)
    assert figure.data[1].x[0] == pytest.approx(46909.971)
    assert figure.data[0].customdata[0][0] == pytest.approx(4.75)
    assert figure.data[0].customdata[0][1] == pytest.approx(0.0)
    assert "Elapsed from period start" in figure.data[0].hovertemplate


def test_show_eeli_keeps_lower_subplot_when_results_are_empty():
    source = make_sequence(np.arange(0.0, 10.1, 0.02), label="timpel_dataset", vendor=Vendor.TIMPEL, sample_frequency=50.0)
    period = make_sequence([10.0, 10.02, 10.04], label="Period 0", vendor=Vendor.TIMPEL, sample_frequency=50.0)

    loaded_data = LoadedData()
    loaded_data.add_sequence(source)
    loaded_data.add_stable_period(period, 0, 0)

    eeli_results = [
        {
            "index": 0,
            "time": np.array([]),
            "values": np.array([]),
            "mean": None,
            "median": None,
            "standard deviation": None,
        },
    ]

    with patch.object(analyze_callbacks, "data_object", new=loaded_data), patch.object(
        analyze_callbacks,
        "eeli",
        new=eeli_results,
    ):
        figure, _ = analyze_callbacks.show_eeli(0, 1)

    assert len(figure.data) == 2
    assert figure.data[0].x[0] == pytest.approx(10.0)
    assert list(figure.data[1].x) == []
    assert list(figure.data[1].y) == []
    assert figure.layout.yaxis2.title.text == "EELI (a.u.)"
    assert figure.layout.xaxis2.title.text == "Dataset time (s)"
