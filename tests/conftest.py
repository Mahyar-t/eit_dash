import os
from pathlib import Path

import pytest
from eitprocessing.datahandling.loading import load_eit_data

environment = os.environ.get(
    "TEST_DATA",
    Path.resolve(Path(__file__).parent.parent),
)

base_directory = Path(environment)
tests_data_path = base_directory / "tests" / "test_data" / "Draeger_Test3.bin"
repo_data_path = base_directory / "test_data" / "draeger_20Hz_healthy_volunteer.bin"
data_path = tests_data_path if tests_data_path.exists() else repo_data_path


@pytest.fixture(scope="session")
def file_data():
    return load_eit_data(
        data_path,
        vendor="draeger",
        label="selected data",
    )
