import json
from pathlib import Path

import pytest


@pytest.fixture
def test_files_dir() -> Path:
    return Path(__file__).parent.joinpath("test_files")


@pytest.fixture()
def simple_data(test_files_dir: Path) -> dict:
    with test_files_dir.joinpath("small_game_data.json").open("r") as small_game_data:
        return json.load(small_game_data)
