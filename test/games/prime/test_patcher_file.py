import copy
import dataclasses
import json
from unittest.mock import MagicMock, patch, ANY

import pytest

import randovania
from randovania.game_description import default_database
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.game_description.resources.pickup_entry import PickupModel, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.games.patchers import claris_patcher_file
from randovania.games.prime.patcher_file_lib import pickup_exporter
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.prime2.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.layout.prime2.hint_configuration import SkyTempleKeyHintMode, HintConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.lib.teleporters import TeleporterShuffleMode


def test_add_header_data_to_result():
    # Setup
    description = MagicMock()
    description.shareable_word_hash = "<shareable_word_hash>"
    description.shareable_hash = "<shareable_hash>"
    expected = {
        "permalink": "-permalink-",
        "seed_hash": "- <shareable_word_hash> (<shareable_hash>)",
        "randovania_version": randovania.VERSION,
        'shareable_hash': '<shareable_hash>',
        'shareable_word_hash': '<shareable_word_hash>',
    }
    result = {}

    # Run
    claris_patcher_file._add_header_data_to_result(description, result)

    # Assert
    assert json.loads(json.dumps(result)) == expected


def test_create_spawn_point_field(echoes_resource_database, empty_patches):
    # Setup
    patches = empty_patches.assign_starting_location(AreaLocation(100, 5000)).assign_extra_initial_items({
        echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 15): 3,
    })

    capacities = [
        {'amount': 3 if item.index == 15 else 0, 'index': item.index}
        for item in echoes_resource_database.item
    ]

    # Run
    result = claris_patcher_file._create_spawn_point_field(patches, echoes_resource_database)

    # Assert
    assert result == {
        "location": {
            "world_asset_id": 100,
            "area_asset_id": 5000,
        },
        "amount": capacities,
        "capacity": capacities,
    }


def test_create_elevators_field_no_elevator(empty_patches, echoes_game_description):
    # Setup
    # Run
    with pytest.raises(ValueError) as exp:
        claris_patcher_file._create_elevators_field(empty_patches, echoes_game_description)

    # Assert
    assert str(exp.value) == "Invalid elevator count. Expected 22, got 0."


@pytest.mark.parametrize("vanilla_gateway", [False, True])
def test_create_elevators_field_elevators_for_a_seed(vanilla_gateway: bool,
                                                     echoes_game_description, empty_patches):
    # Setup
    patches = echoes_game_description.create_game_patches()

    elevator_connection = copy.copy(patches.elevator_connection)
    elevator_connection[Teleporter(0x3BFA3EFF, 0xADED752E, 0x9001B)] = AreaLocation(464164546, 900285955)
    elevator_connection[Teleporter(0x3BFA3EFF, 0x62FF94EE, 0x180086)] = AreaLocation(1039999561, 3479543630)

    if not vanilla_gateway:
        elevator_connection[Teleporter(0x3BFA3EFF, 0x87D35EE4, 0x82A008B)] = AreaLocation(2252328306, 3619928121)

    patches = dataclasses.replace(patches, elevator_connection=elevator_connection)

    # Run
    result = claris_patcher_file._create_elevators_field(patches, echoes_game_description)

    # Assert
    expected = [
        {"instance_id": 589851,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Spider side"},

        {"instance_id": 1572998,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Temple Access"},

        {"instance_id": 1966093,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
         "room_name": "Transport to Torvus Entrance"},

        {"instance_id": 2097251,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
         "target_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
         "room_name": "Transport to Temple Transport Violet"},

        {"instance_id": 136970379,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2278776548},
         "target_location": {"world_asset_id": 2252328306,
                             "area_asset_id": 2068511343 if vanilla_gateway else 3619928121},
         "room_name": "Sky Temple Gateway" if vanilla_gateway else "Transport to Sanctum"},

        {"instance_id": 3342446,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
         "room_name": "Transport to Sanctuary Entrance"},

        {"instance_id": 3538975,
         "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
         "target_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
         "room_name": "Transport to Temple Transport Emerald"},

        {"instance_id": 152,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
         "room_name": "Transport to Sanctuary Quadrant"},

        {"instance_id": 393260,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2556480432},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
         "room_name": "Transport to Torvus Quadrant"},

        {"instance_id": 524321,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
         "room_name": "Transport to Agon Quadrant"},

        {'instance_id': 589949,
         'origin_location': {'area_asset_id': 2068511343, 'world_asset_id': 2252328306},
         'target_location': {'area_asset_id': 2278776548, 'world_asset_id': 1006255871},
         'room_name': 'Sky Temple Energy Controller'},

        {"instance_id": 122,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 1473133138},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
         "room_name": "Transport to Agon Gate"},

        {"instance_id": 1245307,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "room_name": "Transport to Torvus Temple Access"},

        {"instance_id": 2949235,
         "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "room_name": "Transport to Sanctuary Spider side"},

        {"instance_id": 129,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
         "room_name": "Transport to Torvus Gate"},

        {"instance_id": 2162826,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
         "target_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
         "room_name": "Transport to Agon Portal Access"},

        {"instance_id": 4522032,
         "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
         "target_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
         "room_name": "Transport to Sanctuary Vault side"},

        {"instance_id": 38,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
         "room_name": "Transport to Sanctuary Gate"},

        {"instance_id": 1245332,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
         "target_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
         "room_name": "Transport to Agon Temple Access"},

        {"instance_id": 1638535,
         "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
         "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
         "room_name": "Transport to Lower Torvus Access"},

        {'instance_id': 204865660,
         'origin_location': {'world_asset_id': 464164546, 'area_asset_id': 3136899603},
         'target_location': {'world_asset_id': 464164546, 'area_asset_id': 1564082177},
         'room_name': 'Aerie Transport Station'},

        {'instance_id': 4260106,
         'origin_location': {'world_asset_id': 464164546, 'area_asset_id': 1564082177},
         'target_location': {'world_asset_id': 464164546, 'area_asset_id': 3136899603},
         'room_name': 'Aerie'}
    ]
    assert result == expected


def test_create_translator_gates_field():
    # Setup
    gate_assignment = {
        TranslatorGate(1): SimpleResourceInfo(10, "LongA", "A", ResourceType.ITEM),
        TranslatorGate(3): SimpleResourceInfo(50, "LongB", "B", ResourceType.ITEM),
        TranslatorGate(4): SimpleResourceInfo(10, "LongA", "A", ResourceType.ITEM),
    }

    # Run
    result = claris_patcher_file._create_translator_gates_field(gate_assignment)

    # Assert
    assert result == [
        {"gate_index": 1, "translator_index": 10},
        {"gate_index": 3, "translator_index": 50},
        {"gate_index": 4, "translator_index": 10},
    ]


@pytest.mark.parametrize("elevators", [TeleporterShuffleMode.VANILLA, TeleporterShuffleMode.TWO_WAY_RANDOMIZED])
def test_apply_translator_gate_patches(elevators):
    # Setup
    target = {}

    # Run
    claris_patcher_file._apply_translator_gate_patches(target, elevators)

    # Assert
    assert target == {
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": elevators != TeleporterShuffleMode.VANILLA,
    }


def test_get_single_hud_text_locked_pbs():
    # Run
    result = pickup_exporter._get_single_hud_text("Locked Power Bomb Expansion",
                                                  claris_patcher_file._simplified_memo_data(),
                                                  tuple())

    # Assert
    assert result == "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."


def test_pickup_data_for_seeker_launcher(echoes_item_database, echoes_resource_database, randomizer_data):
    # Setup
    state = MajorItemState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_items=0,
        included_ammo=(5,),
    )
    pickup = pickup_creator.create_major_item(
        echoes_item_database.major_items["Seeker Launcher"],
        state,
        True,
        echoes_resource_database,
        echoes_item_database.ammo["Missile Expansion"],
        True
    )
    creator = pickup_exporter.PickupExporterSolo(claris_patcher_file._simplified_memo_data())

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = claris_patcher_file.echoes_pickup_details_to_patcher(
        details, MagicMock(),
        claris_patcher_file._get_model_mapping(randomizer_data))

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Seeker Launcher",
        "model_index": 25,
        "hud_text": ["Seeker Launcher acquired, but the Missile Launcher is required to use it.",
                     "Seeker Launcher acquired!"],
        "sound_index": 0,
        "jingle_index": 1,
        'resources': [{'amount': 5, 'index': 71},
                      {'amount': 1, 'index': 47},
                      {'amount': 1, 'index': 26}],
        "conditional_resources": [
            {'item': 73,
             'resources': [{'amount': 5, 'index': 44},
                           {'amount': 1, 'index': 47},
                           {'amount': 1, 'index': 26}]}
        ],
        "convert": [],
    }


@pytest.mark.parametrize("simplified", [False, True])
def test_pickup_data_for_pb_expansion_locked(simplified, echoes_item_database, echoes_resource_database,
                                             randomizer_data):
    # Setup
    pickup = pickup_creator.create_ammo_expansion(
        echoes_item_database.ammo["Power Bomb Expansion"],
        [2],
        True,
        echoes_resource_database,
    )
    if simplified:
        memo = claris_patcher_file._simplified_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired, but the main Power Bomb is required to use it.",
            "Power Bomb Expansion acquired!",
        ]
    else:
        memo = default_database.default_prime2_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired! \n"
            "Without the main Power Bomb item, you are still unable to release Power Bombs.",
            "Power Bomb Expansion acquired! \nMaximum Power Bomb carrying capacity increased by 2.",
        ]

    creator = pickup_exporter.PickupExporterSolo(memo)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = claris_patcher_file.echoes_pickup_details_to_patcher(
        details, MagicMock(),
        claris_patcher_file._get_model_mapping(randomizer_data))

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage",
        "model_index": 21,
        "hud_text": hud_text,
        "sound_index": 0,
        "jingle_index": 0,
        'resources': [{'amount': 2, 'index': 72},
                      {'amount': 1, 'index': 47}],
        "conditional_resources": [
            {'item': 43,
             'resources': [{'amount': 2, 'index': 43},
                           {'amount': 1, 'index': 47}]}
        ],
        "convert": [],
    }


def test_pickup_data_for_pb_expansion_unlocked(echoes_item_database, echoes_resource_database, randomizer_data):
    # Setup
    pickup = pickup_creator.create_ammo_expansion(
        echoes_item_database.ammo["Power Bomb Expansion"],
        [2],
        False,
        echoes_resource_database,
    )
    creator = pickup_exporter.PickupExporterSolo(claris_patcher_file._simplified_memo_data())

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = claris_patcher_file.echoes_pickup_details_to_patcher(
        details, MagicMock(),
        claris_patcher_file._get_model_mapping(randomizer_data))

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage",
        "model_index": 21,
        "hud_text": ["Power Bomb Expansion acquired!"],
        "sound_index": 0,
        "jingle_index": 0,
        'resources': [{'amount': 2, 'index': 43},
                      {'amount': 1, 'index': 47}],
        "conditional_resources": [],
        "convert": [],
    }


@pytest.mark.parametrize("disable_hud_popup", [False, True])
def test_create_pickup_all_from_pool(echoes_resource_database,
                                     default_layout_configuration,
                                     disable_hud_popup: bool
                                     ):
    item_pool = pool_creator.calculate_pool_results(default_layout_configuration,
                                                    echoes_resource_database)
    index = PickupIndex(0)
    if disable_hud_popup:
        memo_data = claris_patcher_file._simplified_memo_data()
    else:
        memo_data = default_prime2_memo_data()
    creator = pickup_exporter.PickupExporterSolo(memo_data)

    for item in item_pool.pickups:
        data = creator.export(index, PickupTarget(item, 0), item, PickupModelStyle.ALL_VISIBLE)
        for hud_text in data.hud_text:
            assert not hud_text.startswith("Locked")


def test_run_validated_hud_text(randomizer_data):
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    details = pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        scan_text="scan",
        hud_text=["Energy Transfer Module acquired!"],
        conditional_resources=[
            ConditionalResources(None, None, ()),
        ],
        conversion=[],
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
    )

    # Run
    data = claris_patcher_file.echoes_pickup_details_to_patcher(
        details, rng,
        claris_patcher_file._get_model_mapping(randomizer_data))

    # Assert
    assert data['hud_text'] == ['Run validated!']


@pytest.mark.parametrize("stk_mode", SkyTempleKeyHintMode)
@patch("randovania.games.patchers.claris_patcher_file._logbook_title_string_patches", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.hints.create_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.hide_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.create_hints", autospec=True)
def test_create_string_patches(mock_stk_create_hints: MagicMock,
                               mock_stk_hide_hints: MagicMock,
                               mock_item_create_hints: MagicMock,
                               mock_logbook_title_string_patches: MagicMock,
                               stk_mode: SkyTempleKeyHintMode,
                               mocker,
                               ):
    # Setup
    game = MagicMock()
    all_patches = MagicMock()
    rng = MagicMock()
    mock_item_create_hints.return_value = ["item", "hints"]
    mock_stk_create_hints.return_value = ["show", "hints"]
    mock_stk_hide_hints.return_value = ["hide", "hints"]
    player_config = PlayersConfiguration(0, {0: "you"})
    mock_logbook_title_string_patches.return_values = []
    area_namers = MagicMock()

    # Run
    result = claris_patcher_file._create_string_patches(
        HintConfiguration(sky_temple_keys=stk_mode),
        game,
        all_patches,
        area_namers,
        player_config,
        rng,
    )

    # Assert
    expected_result = ["item", "hints"]
    mock_item_create_hints.assert_called_once_with(all_patches, player_config, game.world_list, area_namers, rng)
    mock_logbook_title_string_patches.assert_called_once_with()

    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        mock_stk_hide_hints.assert_called_once_with()
        mock_stk_create_hints.assert_not_called()
        expected_result.extend(["hide", "hints"])

    else:
        mock_stk_create_hints.assert_called_once_with(all_patches, player_config, game.resource_database,
                                                      area_namers, stk_mode == SkyTempleKeyHintMode.HIDE_AREA)
        mock_stk_hide_hints.assert_not_called()
        expected_result.extend(["show", "hints"])

    assert result == expected_result


def test_create_claris_patcher_file(test_files_dir, randomizer_data):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))
    player_index = 0
    preset = description.permalink.get_preset(player_index)
    cosmetic_patches = EchoesCosmeticPatches()

    # Run
    result = claris_patcher_file.create_patcher_file(description, PlayersConfiguration(player_index, {0: "you"}),
                                                     cosmetic_patches, randomizer_data)

    # Assert
    assert isinstance(result["spawn_point"], dict)

    assert isinstance(result["pickups"], list)
    assert len(result["pickups"]) == 119

    assert isinstance(result["elevators"], list)
    assert len(result["elevators"]) == 22

    assert isinstance(result["translator_gates"], list)
    assert len(result["translator_gates"]) == 17

    assert isinstance(result["string_patches"], list)
    assert len(result["string_patches"]) == 60

    assert result["specific_patches"] == {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": preset.configuration.warp_to_start,
        "credits_length": 75 if cosmetic_patches.speed_up_credits else 259,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": preset.configuration.varia_suit_damage,
        "dark_world_dark_suit_damage": preset.configuration.dark_suit_damage,
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": False,
    }
    # TODO: check all fields?
    assert result["dol_patches"]["default_items"] == {
        "visor": "Combat Visor",
        "beam": "Power Beam",
    }
