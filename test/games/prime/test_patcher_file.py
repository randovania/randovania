import copy
import dataclasses
import json
from random import Random
from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest

import randovania
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import ConditionalResources, PickupEntry, ResourceConversion
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.games.prime import patcher_file, default_data
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.layout.hint_configuration import SkyTempleKeyHintMode, HintConfiguration
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.patcher_configuration import PickupModelStyle, PickupModelDataSource
from randovania.layout.translator_configuration import TranslatorConfiguration


def test_add_header_data_to_result():
    # Setup
    description = MagicMock()
    description.permalink.as_str = "<permalink>"
    description.shareable_hash = "<shareable_hash>"
    expected = {
        "permalink": "<permalink>",
        "seed_hash": "<shareable_hash>",
        "randovania_version": randovania.VERSION,
    }
    result = {}

    # Run
    patcher_file._add_header_data_to_result(description, result)

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
    result = patcher_file._create_spawn_point_field(patches, echoes_resource_database)

    # Assert
    assert result == {
        "location": {
            "world_asset_id": 100,
            "area_asset_id": 5000,
        },
        "amount": capacities,
        "capacity": capacities,
    }


def test_create_elevators_field_no_elevator(empty_patches):
    # Setup
    game = data_reader.decode_data(default_data.decode_default_prime2())

    # Run
    with pytest.raises(ValueError) as exp:
        patcher_file._create_elevators_field(empty_patches, game)

    # Assert
    assert str(exp.value) == "Invalid elevator count. Expected 20, got 0."


@pytest.mark.parametrize("vanilla_gateway", [False, True])
def test_create_elevators_field_elevators_for_a_seed(vanilla_gateway: bool,
                                                     echoes_resource_database, empty_patches):
    # Setup
    game = data_reader.decode_data(default_data.decode_default_prime2())
    patches = GamePatches.with_game(game)

    elevator_connection = copy.copy(patches.elevator_connection)
    elevator_connection[589851] = AreaLocation(464164546, 900285955)
    elevator_connection[1572998] = AreaLocation(1039999561, 3479543630)

    if not vanilla_gateway:
        elevator_connection[136970379] = AreaLocation(2252328306, 3619928121)

    patches = dataclasses.replace(patches, elevator_connection=elevator_connection)

    # Run
    result = patcher_file._create_elevators_field(patches, game)

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

        {"instance_id": 589949,
         "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2068511343},
         "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2278776548},
         "room_name": "Sky Temple Energy Controller"},

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
         "room_name": "Transport to Lower Torvus Access"}
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
    result = patcher_file._create_translator_gates_field(gate_assignment)

    # Assert
    assert result == [
        {"gate_index": 1, "translator_index": 10},
        {"gate_index": 3, "translator_index": 50},
        {"gate_index": 4, "translator_index": 10},
    ]


def test_apply_translator_gate_patches():
    # Setup
    target = {}
    translator_gates = TranslatorConfiguration(
        {},
        fixed_gfmc_compound=MagicMock(),
        fixed_torvus_temple=MagicMock(),
        fixed_great_temple=MagicMock(),
    )

    # Run
    patcher_file._apply_translator_gate_patches(target, translator_gates)

    # Assert
    assert target == {
        "always_up_gfmc_compound": translator_gates.fixed_gfmc_compound,
        "always_up_torvus_temple": translator_gates.fixed_torvus_temple,
        "always_up_great_temple": translator_gates.fixed_great_temple,
    }


@pytest.mark.parametrize("order", [
    ("X", "Y"),
    ("Y", "X"),
    ("Y", "Z"),
])
def test_calculate_hud_text(order: Tuple[str, str]):
    # Setup
    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)

    pickup_x = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                           (
                               ConditionalResources("A", None, ((resource_a, 1),)),
                           ))
    pickup_y = PickupEntry("Y", 2, ItemCategory.SUIT,
                           (
                               ConditionalResources("B", None, ((resource_b, 1),)),
                               ConditionalResources("A", resource_b, ((resource_a, 5),))
                           ))
    pickup_z = PickupEntry("Z", 2, ItemCategory.SUIT,
                           (
                               ConditionalResources("A", None, ((resource_a, 1),)),
                               ConditionalResources("B", resource_a, ((resource_b, 5),))
                           ))

    memo_data = {
        "A": "You got {A} of A",
        "B": "You found {B} of B",
    }
    pickups = {
        "X": pickup_x,
        "Y": pickup_y,
        "Z": pickup_z,
    }

    # Run
    result = patcher_file._calculate_hud_text(pickups[order[0]], pickups[order[1]], PickupModelStyle.HIDE_ALL,
                                              memo_data)

    # Assert
    if order[1] == "Y":
        assert result == ["You found 1 of B"]
    elif order[1] == "X":
        assert result == ["You got 1 of A", "You got 1 of A"]
    else:
        assert result == ["You got 1 of A", "You found 5 of B"]


@pytest.mark.parametrize("model_style", PickupModelStyle)
def test_create_pickup_list(model_style: PickupModelStyle, empty_patches):
    # Setup
    has_scan_text = model_style in {PickupModelStyle.ALL_VISIBLE, PickupModelStyle.HIDE_MODEL}
    rng = Random(5000)

    useless_resource = SimpleResourceInfo(0, "Useless", "Useless", ResourceType.ITEM)
    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)
    pickup_a = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY,
                           (
                               ConditionalResources(None, None, ((resource_a, 1),)),
                           ))
    pickup_b = PickupEntry("B", 2, ItemCategory.SUIT,
                           (
                               ConditionalResources(None, None, ((resource_b, 1), (resource_a, 1))),
                               ConditionalResources(None, resource_b, ((resource_a, 5),))
                           ))
    pickup_c = PickupEntry("C", 2, ItemCategory.EXPANSION,
                           resources=(
                               ConditionalResources(None, None, ((resource_b, 2), (resource_a, 1))),
                           ),
                           convert_resources=(
                               ResourceConversion(useless_resource, resource_a),
                           ))

    useless_pickup = PickupEntry("Useless", 0, ItemCategory.ETM,
                                 (
                                     ConditionalResources(None, None, ((useless_resource, 1),)),
                                 ))
    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(0): pickup_a,
        PickupIndex(2): pickup_b,
        PickupIndex(3): pickup_a,
        PickupIndex(4): pickup_c,
    })

    # Run
    result = patcher_file._create_pickup_list(patches, useless_pickup, 5,
                                              rng,
                                              model_style,
                                              PickupModelDataSource.ETM,
                                              None,
                                              )

    # Assert
    assert len(result) == 5
    assert result[0] == {
        "pickup_index": 0,
        "model_index": 1 if model_style == PickupModelStyle.ALL_VISIBLE else 30,
        "scan": "A" if has_scan_text else "Unknown item",
        "hud_text": ["A acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ['Unknown item acquired!'],
        "sound_index": 1 if model_style == PickupModelStyle.ALL_VISIBLE else 0,
        "jingle_index": 2 if model_style == PickupModelStyle.ALL_VISIBLE else 0,
        "resources": [
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[1] == {
        "pickup_index": 1,
        "scan": "Useless" if has_scan_text else "Unknown item",
        "model_index": 0 if model_style == PickupModelStyle.ALL_VISIBLE else 30,
        "hud_text": ["Useless acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ['Unknown item acquired!'],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [
            {
                "index": 0,
                "amount": 1
            }
        ],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[2] == {
        "pickup_index": 2,
        "scan": "B" if has_scan_text else "Unknown item",
        "model_index": 2 if model_style == PickupModelStyle.ALL_VISIBLE else 30,
        "hud_text": ["B acquired!", "B acquired!"] if model_style != PickupModelStyle.HIDE_ALL else [
            'Unknown item acquired!', 'Unknown item acquired!'],
        "sound_index": 0,
        "jingle_index": 1 if model_style == PickupModelStyle.ALL_VISIBLE else 0,
        "resources": [
            {
                "index": 2,
                "amount": 1
            },
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": [{
            "item": 2,
            "resources": [
                {
                    "index": 1,
                    "amount": 5
                }
            ]
        }],
        "convert": [],
    }
    assert result[3] == {
        "pickup_index": 3,
        "scan": "A" if has_scan_text else "Unknown item",
        "model_index": 1 if model_style == PickupModelStyle.ALL_VISIBLE else 30,
        "hud_text": ["A acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ['Unknown item acquired!'],
        "sound_index": 1 if model_style == PickupModelStyle.ALL_VISIBLE else 0,
        "jingle_index": 2 if model_style == PickupModelStyle.ALL_VISIBLE else 0,
        "resources": [
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[4] == {
        "pickup_index": 4,
        "scan": "C that provides 2 B, 1 A" if has_scan_text else "Unknown item",
        "model_index": 2 if model_style == PickupModelStyle.ALL_VISIBLE else 30,
        "hud_text": ["C acquired!"] if model_style != PickupModelStyle.HIDE_ALL else ['Unknown item acquired!'],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [
            {
                "index": 2,
                "amount": 2
            },
            {
                "index": 1,
                "amount": 1
            }
        ],
        "conditional_resources": [],
        "convert": [
            {
                "from_item": 0,
                "to_item": 1,
                "clear_source": True,
                "overwrite_target": False,
            }
        ],
    }


@pytest.mark.parametrize("has_memo_data", [False, True])
def test_create_pickup_list_random_data_source(has_memo_data: bool, empty_patches):
    # Setup
    rng = Random(5000)
    resources = (ConditionalResources(None, None, tuple()),)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)

    pickup_a = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY, resources)
    pickup_b = PickupEntry("B", 2, ItemCategory.SUIT, (ConditionalResources(None, None, tuple()),
                                                       ConditionalResources(None, resource_b, tuple()),))
    pickup_c = PickupEntry("C", 2, ItemCategory.EXPANSION, resources)
    useless_pickup = PickupEntry("Useless", 0, ItemCategory.ETM, resources)

    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(0): pickup_a,
        PickupIndex(2): pickup_b,
        PickupIndex(3): pickup_a,
        PickupIndex(4): pickup_c,
    })

    if has_memo_data:
        memo_data = {
            "A": "This is an awesome item A",
            "B": "This is B. It is good.",
            "C": "What a nice day to have a C",
            "Useless": "Try again next time",
        }
    else:
        memo_data = {
            name: "{} acquired!".format(name)
            for name in ("A", "B", "C", "Useless")
        }

    # Run
    result = patcher_file._create_pickup_list(patches, useless_pickup, 5,
                                              rng,
                                              PickupModelStyle.HIDE_ALL,
                                              PickupModelDataSource.RANDOM,
                                              memo_data if has_memo_data else None,
                                              )

    # Assert
    # Assert
    assert len(result) == 5
    assert result[0] == {
        "pickup_index": 0,
        "model_index": 1,
        "scan": "A",
        "hud_text": [memo_data["A"]],
        "sound_index": 1,
        "jingle_index": 2,
        "resources": [],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[1] == {
        "pickup_index": 1,
        "scan": "A",
        "model_index": 1,
        "hud_text": [memo_data["A"]],
        "sound_index": 1,
        "jingle_index": 2,
        "resources": [],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[2] == {
        "pickup_index": 2,
        "scan": "C",
        "model_index": 2,
        "hud_text": [memo_data["C"], memo_data["C"]],
        "sound_index": 0,
        "jingle_index": 0,
        "resources": [],
        "conditional_resources": [{'item': 2, 'resources': []}],
        "convert": [],
    }
    assert result[3] == {
        "pickup_index": 3,
        "scan": "B",
        "model_index": 2,
        "hud_text": [memo_data["B"]],
        "sound_index": 0,
        "jingle_index": 1,
        "resources": [],
        "conditional_resources": [],
        "convert": [],
    }
    assert result[4] == {
        "pickup_index": 4,
        "scan": "A",
        "model_index": 1,
        "hud_text": [memo_data["A"]],
        "sound_index": 1,
        "jingle_index": 2,
        "resources": [],
        "conditional_resources": [],
        "convert": [],
    }


def test_pickup_scan_for_progressive_suit(echoes_item_database, echoes_resource_database):
    # Setup
    progressive_suit = echoes_item_database.major_items["Progressive Suit"]
    pickup = pickup_creator.create_major_item(progressive_suit, MajorItemState(), False, echoes_resource_database,
                                              None, False)

    # Run
    result = patcher_file._pickup_scan(pickup)

    # Assert
    assert result == "Progressive Suit: Provides the following in order: Dark Suit, Light Suit"


@pytest.mark.parametrize("disable_hud_popup", [False, True])
def test_create_pickup_all_from_pool(echoes_resource_database,
                                     disable_hud_popup: bool
                                     ):
    layout_configuration = LayoutConfiguration.from_params()
    item_pool = pool_creator.calculate_pool_results(layout_configuration, echoes_resource_database)[0]
    index = PickupIndex(0)
    if disable_hud_popup:
        memo_data = None
    else:
        memo_data = default_prime2_memo_data()

    for item in item_pool:
        try:
            patcher_file._create_pickup(index, item, item, PickupModelStyle.ALL_VISIBLE, memo_data)
        except Exception as e:
            assert str(e) == item.name


@pytest.mark.parametrize("stk_mode", SkyTempleKeyHintMode)
@patch("randovania.games.prime.patcher_file_lib.item_hints.create_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.hide_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.create_hints", autospec=True)
def test_create_string_patches(mock_stk_create_hints: MagicMock,
                               mock_stk_hide_hints: MagicMock,
                               mock_item_create_hints: MagicMock,
                               stk_mode: SkyTempleKeyHintMode,
                               ):
    # Setup
    game = MagicMock()
    patches = MagicMock()
    rng = MagicMock()
    mock_item_create_hints.return_value = ["item", "hints"]
    mock_stk_create_hints.return_value = ["show", "hints"]
    mock_stk_hide_hints.return_value = ["hide", "hints"]

    # Run
    result = patcher_file._create_string_patches(HintConfiguration(sky_temple_keys=stk_mode),
                                                 game,
                                                 patches,
                                                 rng)

    # Assert
    expected_result = ["item", "hints"]
    mock_item_create_hints.assert_called_once_with(patches, game.world_list, rng)

    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        mock_stk_hide_hints.assert_called_once_with()
        mock_stk_create_hints.assert_not_called()
        expected_result.extend(["hide", "hints"])

    else:
        mock_stk_create_hints.assert_called_once_with(patches, game.world_list,
                                                      stk_mode == SkyTempleKeyHintMode.HIDE_AREA)
        mock_stk_hide_hints.assert_not_called()
        expected_result.extend(["show", "hints"])

    assert result == expected_result


def test_create_patcher_file(test_files_dir):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.json"))
    cosmetic_patches = CosmeticPatches()
    translator_gates = description.permalink.layout_configuration.translator_configuration

    # Run
    result = patcher_file.create_patcher_file(description, cosmetic_patches)

    # Assert
    assert isinstance(result["spawn_point"], dict)

    assert isinstance(result["pickups"], list)
    assert len(result["pickups"]) == 119

    assert isinstance(result["elevators"], list)
    assert len(result["elevators"]) == 20

    assert isinstance(result["translator_gates"], list)
    assert len(result["translator_gates"]) == 17

    assert isinstance(result["string_patches"], list)
    assert len(result["string_patches"]) == 40

    assert result["specific_patches"] == {
        "hive_chamber_b_post_state": True,
        "intro_in_post_state": True,
        "warp_to_start": description.permalink.patcher_configuration.warp_to_start,
        "speed_up_credits": cosmetic_patches.speed_up_credits,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": description.permalink.patcher_configuration.varia_suit_damage,
        "dark_world_dark_suit_damage": description.permalink.patcher_configuration.dark_suit_damage,
        "always_up_gfmc_compound": translator_gates.fixed_gfmc_compound,
        "always_up_torvus_temple": translator_gates.fixed_torvus_temple,
        "always_up_great_temple": translator_gates.fixed_great_temple,
    }
