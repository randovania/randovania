import dataclasses
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.resources import ResourceDatabase


@pytest.fixture
def test_files_dir() -> Path:
    return Path(__file__).parent.joinpath("test_files")


@pytest.fixture()
def simple_data(test_files_dir: Path) -> dict:
    with test_files_dir.joinpath("small_game_data.json").open("r") as small_game_data:
        return json.load(small_game_data)


@pytest.fixture()
def echoes_resource_database() -> ResourceDatabase:
    return default_database.default_prime2_resource_database()


@pytest.fixture()
def echoes_item_database() -> ItemDatabase:
    return default_database.default_prime2_item_database()


class DataclassTestLib:
    def mock_dataclass(self, obj) -> MagicMock:
        return MagicMock(spec=[field.name for field in dataclasses.fields(obj)])


@pytest.fixture()
def dataclass_test_lib() -> DataclassTestLib:
    return DataclassTestLib()


@pytest.fixture()
def empty_patches() -> GamePatches:
    return GamePatches({}, {}, {}, {}, (), None)


def pytest_addoption(parser):
    parser.addoption('--skip-generation-tests', action='store_true', dest="skip_generation_tests",
                     default=False, help="Skips running layout generation tests")
    parser.addoption('--skip-gui-tests', action='store_true', dest="skip_gui_tests",
                     default=False, help="Skips running GUI tests")
