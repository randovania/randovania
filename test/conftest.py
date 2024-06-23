from __future__ import annotations

import asyncio
import dataclasses
import uuid
from importlib.util import find_spec
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, PropertyMock

import pytest
from frozendict import frozendict

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.pickup.pickup_category import PickupCategory
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games import default_data
from randovania.games.blank.layout import BlankConfiguration
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.games.prime2.exporter.claris_randomizer_data import decode_randomizer_data
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.preset import Preset
from randovania.lib import json_lib

if TYPE_CHECKING:
    import pytest_mock

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.resources.resource_database import ResourceDatabase


class TestFilesDir:
    def __init__(self, root: Path):
        self.root = root

    def joinpath(self, *paths) -> Path:
        return self.root.joinpath(*paths)

    def read_json(self, *paths) -> dict | list:
        return json_lib.read_path(self.joinpath(*paths))


@pytest.fixture(scope="session")
def test_files_dir() -> TestFilesDir:
    return TestFilesDir(Path(__file__).parent.joinpath("test_files"))


@pytest.fixture(scope="session")
def echo_tool(request, test_files_dir) -> Path:
    if request.config.option.skip_echo_tool:
        pytest.skip()
    return test_files_dir.joinpath("echo_tool.py")


@pytest.fixture()
def preset_manager(tmp_path) -> PresetManager:
    return PresetManager(tmp_path.joinpath("presets"))


@pytest.fixture(params=[False, True])
def blank_available_in_multi(request) -> bool:
    data = RandovaniaGame.BLANK.data
    old_value = data.defaults_available_in_game_sessions
    try:
        object.__setattr__(data, "defaults_available_in_game_sessions", request.param)
        yield request.param
    finally:
        object.__setattr__(data, "defaults_available_in_game_sessions", old_value)


@pytest.fixture(scope="session")
def default_preset() -> Preset:
    return PresetManager(None).default_preset.get_preset()


@pytest.fixture(scope="session")
def blank_game_data() -> dict:
    return default_data.read_json_then_binary(RandovaniaGame.BLANK)[1]


@pytest.fixture(scope="session")
def default_blank_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.BLANK).get_preset()


@pytest.fixture(scope="session")
def default_blank_configuration(default_blank_preset) -> BlankConfiguration:
    assert isinstance(default_blank_preset.configuration, BlankConfiguration)
    return default_blank_preset.configuration


@pytest.fixture(scope="session")
def blank_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.BLANK)


@pytest.fixture(scope="session")
def blank_resource_db(blank_game_description) -> ResourceDatabase:
    return blank_game_description.resource_database


@pytest.fixture()
def blank_game_patches(default_blank_configuration, blank_game_description) -> GamePatches:
    return GamePatches.create_from_game(blank_game_description, 0, default_blank_configuration)


@pytest.fixture(scope="session")
def customized_preset(default_preset) -> Preset:
    return Preset(
        name=f"{default_preset.name} Custom",
        description="A customized preset.",
        uuid=uuid.uuid4(),
        game=default_preset.game,
        configuration=default_preset.configuration,
    )


@pytest.fixture(scope="session")
def default_prime_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()


@pytest.fixture(scope="session")
def default_echoes_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).get_preset()


@pytest.fixture(scope="session")
def default_echoes_configuration(default_echoes_preset) -> EchoesConfiguration:
    assert isinstance(default_echoes_preset.configuration, EchoesConfiguration)
    return default_echoes_preset.configuration


@pytest.fixture()
def echoes_game_patches(default_echoes_configuration, echoes_game_description) -> GamePatches:
    return GamePatches.create_from_game(echoes_game_description, 0, default_echoes_configuration)


@pytest.fixture(scope="session")
def default_prime_configuration() -> PrimeConfiguration:
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    assert isinstance(preset.configuration, PrimeConfiguration)
    return preset.configuration


@pytest.fixture()
def prime_game_patches(default_prime_configuration, prime_game_description) -> GamePatches:
    return GamePatches.create_from_game(prime_game_description, 0, default_prime_configuration)


@pytest.fixture(scope="session")
def prime1_resource_database() -> ResourceDatabase:
    return default_database.resource_database_for(RandovaniaGame.METROID_PRIME)


@pytest.fixture(scope="session")
def echoes_resource_database() -> ResourceDatabase:
    return default_database.resource_database_for(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def echoes_pickup_database() -> PickupDatabase:
    return default_database.pickup_database_for_game(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def echoes_game_data() -> dict:
    return default_data.read_json_then_binary(RandovaniaGame.METROID_PRIME_ECHOES)[1]


@pytest.fixture(scope="session")
def echoes_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)


@pytest.fixture(scope="session")
def prime_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME)


@pytest.fixture(scope="session")
def corruption_game_data() -> dict:
    return default_data.read_json_then_binary(RandovaniaGame.METROID_PRIME_CORRUPTION)[1]


@pytest.fixture(scope="session")
def corruption_game_description(corruption_game_data) -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PRIME_CORRUPTION)


@pytest.fixture(scope="session")
def dread_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_DREAD)


@pytest.fixture(scope="session")
def am2r_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.AM2R)


@pytest.fixture(scope="session")
def msr_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_SAMUS_RETURNS)


@pytest.fixture(scope="session")
def fusion_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.FUSION)


@pytest.fixture(scope="session")
def default_fusion_preset() -> Preset:
    return PresetManager(None).default_preset_for_game(RandovaniaGame.FUSION).get_preset()


@pytest.fixture(scope="session")
def default_fusion_configuration(default_fusion_preset) -> FusionConfiguration:
    assert isinstance(default_fusion_preset.configuration, FusionConfiguration)
    return default_fusion_preset.configuration


@pytest.fixture()
def fusion_game_patches(default_fusion_configuration, fusion_game_description) -> GamePatches:
    return GamePatches.create_from_game(fusion_game_description, 0, default_fusion_configuration)


@pytest.fixture(scope="session")
def planets_zebeth_game_description() -> GameDescription:
    return default_database.game_description_for(RandovaniaGame.METROID_PLANETS_ZEBETH)


@pytest.fixture(scope="session")
def randomizer_data() -> dict:
    return decode_randomizer_data()


@pytest.fixture(params=RandovaniaGame)
def game_enum(request) -> RandovaniaGame:
    return request.param


@pytest.fixture(params=[False, True])
def is_dev_version(request, mocker) -> bool:
    mocker.patch("randovania.is_dev_version", return_value=request.param)
    return request.param


@pytest.fixture(params=[False, True])
def is_frozen(request, mocker) -> bool:
    mocker.patch("randovania.is_frozen", return_value=request.param)
    if request.param:
        # Mock this call as it fails frequently when frozen
        mocker.patch("randovania.gui.lib.common_qt_lib.set_default_window_icon")

    return request.param


@pytest.fixture()
def generic_pickup_category() -> PickupCategory:
    return PickupCategory(
        name="generic",
        long_name="Generic Item Category",
        hint_details=("an ", "unspecified item"),
        hinted_as_major=False,
    )


@pytest.fixture()
def default_generator_params() -> PickupGeneratorParams:
    return PickupGeneratorParams(
        preferred_location_category=LocationCategory.MAJOR,
    )


@pytest.fixture()
def blank_pickup(echoes_pickup_database, default_generator_params) -> PickupEntry:
    return PickupEntry(
        name="Blank Pickup",
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        pickup_category=echoes_pickup_database.pickup_categories["suit"],
        broad_category=echoes_pickup_database.pickup_categories["life_support"],
        progression=(),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def dread_spider_pickup(default_generator_params) -> PickupEntry:
    dread_pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    return PickupEntry(
        name="Spider Magnet",
        model=PickupModel(
            game=RandovaniaGame.METROID_DREAD,
            name="powerup_spidermagnet",
        ),
        pickup_category=dread_pickup_database.pickup_categories["misc"],
        broad_category=dread_pickup_database.pickup_categories["misc"],
        progression=(
            (
                ItemResourceInfo(
                    resource_index=24,
                    long_name="Spider Magnet",
                    short_name="Magnet",
                    max_capacity=1,
                    extra=frozendict({"item_id": "ITEM_MAGNET_GLOVE"}),
                ),
                1,
            ),
        ),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def msr_ice_beam_pickup(default_generator_params) -> PickupEntry:
    msr_pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_SAMUS_RETURNS)
    return PickupEntry(
        name="Ice Beam",
        model=PickupModel(
            game=RandovaniaGame.METROID_SAMUS_RETURNS,
            name="powerup_icebeam",
        ),
        pickup_category=msr_pickup_database.pickup_categories["misc"],
        broad_category=msr_pickup_database.pickup_categories["misc"],
        progression=(
            (
                ItemResourceInfo(
                    resource_index=24,
                    long_name="Ice Beam",
                    short_name="Ice",
                    max_capacity=1,
                    extra=frozendict({"item_id": "ITEM_WEAPON_ICE_BEAM"}),
                ),
                1,
            ),
        ),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def am2r_varia_pickup(default_generator_params) -> PickupEntry:
    am2r_pickup_database = default_database.pickup_database_for_game(RandovaniaGame.AM2R)
    return PickupEntry(
        name="Varia Suit",
        model=PickupModel(
            game=RandovaniaGame.AM2R,
            name="sItemVariaSuit",
        ),
        pickup_category=am2r_pickup_database.pickup_categories["suit"],
        broad_category=am2r_pickup_database.pickup_categories["life_support"],
        progression=(
            (
                ItemResourceInfo(
                    resource_index=6,
                    long_name="Varia Suit",
                    short_name="Varia Suit",
                    max_capacity=1,
                ),
                1,
            ),
        ),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def cs_panties_pickup(default_generator_params) -> PickupEntry:
    cs_pickup_database = default_database.pickup_database_for_game(RandovaniaGame.CAVE_STORY)
    return PickupEntry(
        name="Curly's Panties",
        model=PickupModel(
            game=RandovaniaGame.CAVE_STORY,
            name="",
        ),
        pickup_category=cs_pickup_database.pickup_categories["useless"],
        broad_category=cs_pickup_database.pickup_categories["useless"],
        progression=(
            (
                ItemResourceInfo(
                    resource_index=22,
                    long_name="Curly's Panties",
                    short_name="panties",
                    max_capacity=1,
                    extra=frozendict(
                        {
                            "it+": 35,
                            "flag": 7133,
                            "trade": "lewd",
                            "text": "Got =Curly's Underwear=!",
                        }
                    ),
                ),
                1,
            ),
        ),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )


@pytest.fixture()
def small_echoes_game_description(test_files_dir) -> GameDescription:
    from randovania.game_description import data_reader

    return data_reader.decode_data(json_lib.read_path(test_files_dir.joinpath("prime2_small.json")))


class DataclassTestLib:
    def mock_dataclass(self, obj) -> MagicMock:
        return MagicMock(spec=[field.name for field in dataclasses.fields(obj)])


@pytest.fixture()
def dataclass_test_lib() -> DataclassTestLib:
    return DataclassTestLib()


@pytest.fixture()
def empty_patches(default_blank_configuration, blank_game_description) -> GamePatches:
    configuration = default_blank_configuration
    return GamePatches.create_from_game(blank_game_description, 0, configuration)


@pytest.fixture()
def _mock_seed_hash(mocker: pytest_mock.MockerFixture):
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash_bytes",
        new_callable=PropertyMock,
        return_value=b"\x00\x00\x00\x00\x00",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
        new_callable=PropertyMock,
        return_value="Some Words",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash",
        new_callable=PropertyMock,
        return_value="XXXXXXXX",
    )


@pytest.fixture()
def obfuscator_test_secret(monkeypatch):
    from randovania.lib import obfuscator

    monkeypatch.setattr(obfuscator, "_secret", "cNGtDlTqCYF3BFCAQTaDSo5O7DQtzjsd3mS801MPM_M=")
    yield None
    obfuscator._encrypt = None


@pytest.fixture()
def obfuscator_no_secret(monkeypatch):
    from randovania.lib import obfuscator

    monkeypatch.setattr(obfuscator, "_secret", None)
    yield None
    obfuscator._encrypt = None


def pytest_addoption(parser):
    parser.addoption(
        "--skip-generation-tests",
        action="store_true",
        dest="skip_generation_tests",
        default=False,
        help="Skips running layout generation tests",
    )
    parser.addoption(
        "--skip-resolver-tests",
        action="store_true",
        dest="skip_resolver_tests",
        default=False,
        help="Skips running validation tests",
    )
    parser.addoption(
        "--skip-gui-tests", action="store_true", dest="skip_gui_tests", default=False, help="Skips running GUI tests"
    )
    parser.addoption(
        "--skip-echo-tool",
        action="store_true",
        dest="skip_echo_tool",
        default=False,
        help="Skips running tests that uses the echo tool",
    )


if all(find_spec(n) is not None for n in ("pytestqt", "qasync")):
    import asyncio.events

    import qasync

    class EventLoopWithRunningFlag(qasync.QEventLoop):
        def _before_run_forever(self):
            super()._before_run_forever()
            asyncio.events._set_running_loop(self)

        def _after_run_forever(self):
            asyncio.events._set_running_loop(None)
            super()._after_run_forever()

    @pytest.fixture()
    def skip_qtbot(request, qtbot):
        if request.config.option.skip_gui_tests:
            pytest.skip()

        return qtbot

    @pytest.fixture()
    def event_loop(request: pytest.FixtureRequest):
        if "skip_qtbot" in request.fixturenames:
            loop = EventLoopWithRunningFlag(request.getfixturevalue("qapp"), set_running_loop=False)
        else:
            loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()

else:

    @pytest.fixture()
    def skip_qtbot(request):
        pytest.skip()
        return "no qtbot"


def pytest_configure(config: pytest.Config):
    markers = []

    if config.option.skip_generation_tests:
        markers.append("not skip_generation_tests")

    if config.option.skip_resolver_tests:
        markers.append("not skip_resolver_tests")

    if config.option.skip_gui_tests:
        markers.append("not skip_gui_tests")

    config.option.markexpr = " and ".join(markers)
