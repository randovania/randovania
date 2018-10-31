import json

import py
import pytest


@pytest.fixture
def test_files_dir():
    return py.path.local(__file__).new(basename="test_files")


@pytest.fixture()
def simple_data(test_files_dir):
    with test_files_dir.join("small_game_data.json").open("r") as small_game_data:
        return json.load(small_game_data)
