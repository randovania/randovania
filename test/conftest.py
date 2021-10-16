import dataclasses
import json
from pathlib import Path
import uuid
from randovania.game_description.item.item_category import ItemCategory
from unittest.mock import MagicMock

import pytest

import randovania.games.patchers.claris_patcher
from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.preset import Preset
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration


@pytest.fixture(scope="session")
def test_files_dir() -> Path:
    return Path(__file__).parent.joinpath("test_files")


@pytest.fixture(scope="session")
def echo_tool(request, test_files_dir) -> Path:
    if request.config.option.skip_echo_tool:
        pytest.skip()
    return test_files_dir.joinpath("echo_tool.py")


@pytest.fixture()
def preset_manager(tmp_path) -> PresetManager:
    return PresetManager(tmp_path.joinpath("presets"))


@pytest.fixture(scope="session")
def default_preset() -> Preset:
    return PresetManager(None).default_preset.get_preset()

@pytest.fixture(scope="session")
def customized_preset(default_preset) -> Preset:
    return Preset(
        name="{} Custom".format(default_preset.name),
        description="A customized preset.",
        uuid=uuid.uuid4(),
        base_preset_uuid=default_preset.uuid,
        game=default_preset.game,
        configuration=default_preset.configuration
    )

@pytest.fixture(scope="session")
def default_echoes_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()


@pytest.fixture(scope="session")
def default_layout_configuration() -> EchoesConfiguration:
    return PresetManager(None).default_preset.get_preset().configuration


@pytest.fixture(scope="session")
def prime1_resource_database() -> ResourceDatabase:
    return default_database.resource_database_for(RandovaniaGame.METROID_PRIME)


@pytest.fixture(scope="session")
def echoes_resource_database() -> ResourceDatabase:
    return default_database.resource_database_for(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def echoes_item_database() -> ItemDatabase:
    return default_database.item_database_for_game(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def echoes_game_data() -> dict:
    return default_data.read_json_then_binary(RandovaniaGame.METROID_PRIME_ECHOES)[1]


@pytest.fixture(scope="session")
def echoes_game_description(echoes_game_data) -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def corruption_game_data() -> dict:
    return default_data.read_json_then_binary(RandovaniaGame.METROID_PRIME_CORRUPTION)[1]


@pytest.fixture(scope="session")
def corruption_game_description(corruption_game_data) -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_CORRUPTION)


@pytest.fixture(scope="session")
def randomizer_data() -> dict:
    return randovania.games.patchers.claris_patcher.decode_randomizer_data()


@pytest.fixture(params=RandovaniaGame)
def game_enum(request) -> RandovaniaGame:
    return request.param


@pytest.fixture()
def generic_item_category() -> ItemCategory:
    return ItemCategory(
        name="generic",
        long_name="Generic Item Category",
        hint_details=("an ", "unspecified item"),
        is_major=False
    )

@pytest.fixture()
def blank_pickup(echoes_item_database) -> PickupEntry:
    return PickupEntry(
        name="Blank Pickup",
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        item_category=echoes_item_database.item_categories["suit"],
        broad_category=echoes_item_database.item_categories["life_support"],
        progression=(),
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def small_echoes_game_description(test_files_dir) -> GameDescription:
    from randovania.game_description import data_reader
    with test_files_dir.joinpath("prime2_small.json").open("r") as small_game:
        return data_reader.decode_data(json.load(small_game))


class DataclassTestLib:
    def mock_dataclass(self, obj) -> MagicMock:
        return MagicMock(spec=[field.name for field in dataclasses.fields(obj)])


@pytest.fixture()
def dataclass_test_lib() -> DataclassTestLib:
    return DataclassTestLib()


@pytest.fixture()
def empty_patches() -> GamePatches:
    return GamePatches(0, {}, {}, {}, {}, {}, {}, None, {})


def pytest_addoption(parser):
    parser.addoption('--skip-generation-tests', action='store_true', dest="skip_generation_tests",
                     default=False, help="Skips running layout generation tests")
    parser.addoption('--skip-resolver-tests', action='store_true', dest="skip_resolver_tests",
                     default=False, help="Skips running validation tests")
    parser.addoption('--skip-gui-tests', action='store_true', dest="skip_gui_tests",
                     default=False, help="Skips running GUI tests")
    parser.addoption('--skip-echo-tool', action='store_true', dest="skip_echo_tool",
                     default=False, help="Skips running tests that uses the echo tool")


try:
    import pytestqt


    @pytest.fixture()
    def skip_qtbot(request, qtbot):
        if request.config.option.skip_gui_tests:
            pytest.skip()
        return qtbot

except ImportError:
    @pytest.fixture()
    def skip_qtbot(request):
        pytest.skip()


def pytest_configure(config):
    if config.option.skip_generation_tests:
        setattr(config.option, 'markexpr', 'not skip_generation_tests')

    if config.option.skip_resolver_tests:
        setattr(config.option, 'markexpr', 'not skip_resolver_tests')

    if config.option.skip_gui_tests:
        setattr(config.option, 'markexpr', 'not skip_gui_tests')
