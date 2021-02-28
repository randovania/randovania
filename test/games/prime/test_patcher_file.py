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
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.default_database import default_prime2_memo_data
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import ConditionalResources, PickupEntry, ResourceConversion
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.games.prime import patcher_file, default_data
from randovania.generator.item_pool import pickup_creator, pool_creator
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.hint_configuration import SkyTempleKeyHintMode, HintConfiguration
from randovania.layout.elevators import LayoutElevators
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.pickup_model import PickupModelStyle, PickupModelDataSource


def test_add_header_data_to_result():
    # Setup
    description = MagicMock()
    description.shareable_word_hash = "<shareable_word_hash>"
    description.shareable_hash = "<shareable_hash>"
    expected = {
        "permalink": "-permalink-",
        "seed_hash": "- <shareable_word_hash> (<shareable_hash>)",
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
    assert str(exp.value) == "Invalid elevator count. Expected 22, got 0."


@pytest.mark.parametrize("vanilla_gateway", [False, True])
def test_create_elevators_field_elevators_for_a_seed(vanilla_gateway: bool,
                                                     echoes_resource_database, empty_patches):
    # Setup
    game = data_reader.decode_data(default_data.decode_default_prime2())
    patches = game.create_game_patches()

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
    result = patcher_file._create_translator_gates_field(gate_assignment)

    # Assert
    assert result == [
        {"gate_index": 1, "translator_index": 10},
        {"gate_index": 3, "translator_index": 50},
        {"gate_index": 4, "translator_index": 10},
    ]


@pytest.mark.parametrize("elevators", [LayoutElevators.VANILLA, LayoutElevators.TWO_WAY_RANDOMIZED])
def test_apply_translator_gate_patches(elevators):
    # Setup
    target = {}

    # Run
    patcher_file._apply_translator_gate_patches(target, elevators)

    # Assert
    assert target == {
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": elevators != LayoutElevators.VANILLA,
    }


def test_get_single_hud_text_locked_pbs():
    # Run
    result = patcher_file._get_single_hud_text("Temporary Power Bombs", patcher_file._simplified_memo_data(), tuple())

    # Assert
    assert result == "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."


def test_get_single_hud_text_all_major_items(echoes_item_database, echoes_resource_database):
    memo_data = default_prime2_memo_data()

    # Run
    for item in echoes_item_database.major_items.values():
        pickup = pickup_creator.create_major_item(item, MajorItemState(), False, echoes_resource_database, None, False)

        result = patcher_file._get_all_hud_text(pickup, memo_data)
        for i, progression in enumerate(pickup.resources):
            assert progression.name in result[i]
        assert result
        for line in result:
            assert len(line) > 10
            assert isinstance(line, str)


@pytest.mark.parametrize("order", [
    ("X", "Y"),
    ("Y", "X"),
    ("Y", "Z"),
])
def test_calculate_hud_text(order: Tuple[str, str]):
    # Setup
    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)

    pickup_x = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY, ItemCategory.KEY,
                           (
                               ConditionalResources("A", None, ((resource_a, 1),)),
                           ))
    pickup_y = PickupEntry("Y", 2, ItemCategory.SUIT, ItemCategory.LIFE_SUPPORT,
                           (
                               ConditionalResources("B", None, ((resource_b, 1),)),
                               ConditionalResources("A", resource_b, ((resource_a, 5),))
                           ))
    pickup_z = PickupEntry("Z", 2, ItemCategory.SUIT, ItemCategory.LIFE_SUPPORT,
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

    useless_resource = ItemResourceInfo(0, "Useless", "Useless", 10, None)
    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)
    pickup_a = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY, ItemCategory.KEY,
                           (
                               ConditionalResources(None, None, ((resource_a, 1),)),
                           ))
    pickup_b = PickupEntry("B", 2, ItemCategory.SUIT, ItemCategory.LIFE_SUPPORT,
                           (
                               ConditionalResources(None, None, ((resource_b, 1), (resource_a, 1))),
                               ConditionalResources(None, resource_b, ((resource_a, 5),))
                           ))
    pickup_c = PickupEntry("C", 2, ItemCategory.EXPANSION, ItemCategory.MISSILE_RELATED,
                           resources=(
                               ConditionalResources(None, None, ((resource_b, 2), (resource_a, 1))),
                           ),
                           convert_resources=(
                               ResourceConversion(useless_resource, resource_a),
                           ))

    useless_pickup = PickupEntry("Useless", 0, ItemCategory.ETM, ItemCategory.ETM,
                                 (
                                     ConditionalResources(None, None, ((useless_resource, 1),)),
                                 ))
    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(0): PickupTarget(pickup_a, 0),
        PickupIndex(2): PickupTarget(pickup_b, 0),
        PickupIndex(3): PickupTarget(pickup_a, 0),
        PickupIndex(4): PickupTarget(pickup_c, 0),
    })
    creator = patcher_file.PickupCreatorSolo(MagicMock(), patcher_file._SimplifiedMemo())

    # Run
    result = patcher_file._create_pickup_list(patches,
                                              PickupTarget(useless_pickup, 0),
                                              5,
                                              rng,
                                              model_style,
                                              PickupModelDataSource.ETM,
                                              creator,
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
        "scan": "C that provides 2 B and 1 A" if has_scan_text else "Unknown item",
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
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)

    pickup_a = PickupEntry("A", 1, ItemCategory.TEMPLE_KEY, ItemCategory.KEY, resources)
    pickup_b = PickupEntry("B", 2, ItemCategory.SUIT, ItemCategory.LIFE_SUPPORT,
                           (ConditionalResources(None, None, tuple()),
                            ConditionalResources(None, resource_b, tuple()),))
    pickup_c = PickupEntry("C", 2, ItemCategory.EXPANSION, ItemCategory.MISSILE_RELATED, resources)
    useless_pickup = PickupEntry("Useless", 0, ItemCategory.ETM, ItemCategory.ETM, resources)

    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(0): PickupTarget(pickup_a, 0),
        PickupIndex(2): PickupTarget(pickup_b, 0),
        PickupIndex(3): PickupTarget(pickup_a, 0),
        PickupIndex(4): PickupTarget(pickup_c, 0),
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

    creator = patcher_file.PickupCreatorSolo(MagicMock(), memo_data)

    # Run
    result = patcher_file._create_pickup_list(patches,
                                              PickupTarget(useless_pickup, 0),
                                              5,
                                              rng,
                                              PickupModelStyle.HIDE_ALL,
                                              PickupModelDataSource.RANDOM,
                                              creator,
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
    assert result == "Progressive Suit. Provides the following in order: Dark Suit, Light Suit"


@pytest.mark.parametrize("disable_hud_popup", [False, True])
def test_create_pickup_all_from_pool(echoes_resource_database,
                                     default_layout_configuration,
                                     disable_hud_popup: bool
                                     ):
    item_pool = pool_creator.calculate_pool_results(default_layout_configuration,
                                                    echoes_resource_database)
    index = PickupIndex(0)
    if disable_hud_popup:
        memo_data = patcher_file._SimplifiedMemo()
    else:
        memo_data = default_prime2_memo_data()
    creator = patcher_file.PickupCreatorSolo(MagicMock(), memo_data)

    for item in item_pool.pickups:
        creator.create_pickup(index, PickupTarget(item, 0), item, PickupModelStyle.ALL_VISIBLE)


def test_run_validated_hud_text():
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    creator = patcher_file.PickupCreatorSolo(rng, patcher_file._SimplifiedMemo())
    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    pickup = PickupEntry("Energy Transfer Module", 1, ItemCategory.TEMPLE_KEY, ItemCategory.KEY,
                         (
                             ConditionalResources("Energy Transfer Module", None, ((resource_a, 1),)),
                         ))

    # Run
    data = creator.create_pickup_data(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE,
                                      "Scan Text")

    # Assert
    assert data['hud_text'] == ['Run validated!']


@pytest.fixture(name="pickup_for_create_pickup_data")
def _create_pickup_data():
    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)
    return PickupEntry("Cake", 1, ItemCategory.TEMPLE_KEY, ItemCategory.KEY,
                       (
                           ConditionalResources("Sugar", None, ((resource_a, 1),)),
                           ConditionalResources("Salt", resource_a, ((resource_b, 1),)),
                       ))


def test_solo_create_pickup_data(pickup_for_create_pickup_data):
    # Setup
    creator = patcher_file.PickupCreatorSolo(MagicMock(), patcher_file._SimplifiedMemo())

    # Run
    data = creator.create_pickup_data(PickupIndex(10), PickupTarget(pickup_for_create_pickup_data, 0),
                                      pickup_for_create_pickup_data, PickupModelStyle.ALL_VISIBLE,
                                      "Scan Text")

    # Assert
    assert data == {
        'conditional_resources': [
            {'item': 1, 'resources': [{'amount': 1, 'index': 2}]}
        ],
        'convert': [],
        'hud_text': ['Sugar acquired!', 'Salt acquired!'],
        'resources': [{'amount': 1, 'index': 1}],
        'scan': 'Scan Text',
    }


def test_multi_create_pickup_data_for_self(pickup_for_create_pickup_data):
    # Setup
    creator = patcher_file.PickupCreatorMulti(MagicMock(), patcher_file._SimplifiedMemo(),
                                              PlayersConfiguration(0, {0: "You",
                                                                       1: "Someone"}))

    # Run
    data = creator.create_pickup_data(PickupIndex(10), PickupTarget(pickup_for_create_pickup_data, 0),
                                      pickup_for_create_pickup_data, PickupModelStyle.ALL_VISIBLE,
                                      "Scan Text")

    # Assert
    assert data == {
        'conditional_resources': [
            {'item': 1, 'resources': [{'amount': 1, 'index': 2},
                                      {'amount': 11, 'index': 74},
                                      ]}
        ],
        'convert': [],
        'hud_text': ['Sugar acquired!', 'Salt acquired!'],
        'resources': [{'amount': 1, 'index': 1}, {'amount': 11, 'index': 74}, ],
        'scan': 'Your Scan Text',
    }


def test_multi_create_pickup_data_for_other(pickup_for_create_pickup_data):
    # Setup
    creator = patcher_file.PickupCreatorMulti(MagicMock(), patcher_file._SimplifiedMemo(),
                                              PlayersConfiguration(0, {0: "You",
                                                                       1: "Someone"}))

    # Run
    data = creator.create_pickup_data(PickupIndex(10), PickupTarget(pickup_for_create_pickup_data, 1),
                                      pickup_for_create_pickup_data, PickupModelStyle.ALL_VISIBLE,
                                      "Scan Text")

    # Assert
    assert data == {
        'conditional_resources': [],
        'convert': [],
        'hud_text': ['Sent Cake to Someone!'],
        'resources': [{'amount': 11, 'index': 74}, ],
        'scan': "Someone's Scan Text",
    }


@pytest.mark.parametrize("stk_mode", SkyTempleKeyHintMode)
@patch("randovania.games.prime.patcher_file._logbook_title_string_patches", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.item_hints.create_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.hide_hints", autospec=True)
@patch("randovania.games.prime.patcher_file_lib.sky_temple_key_hint.create_hints", autospec=True)
def test_create_string_patches(mock_stk_create_hints: MagicMock,
                               mock_stk_hide_hints: MagicMock,
                               mock_item_create_hints: MagicMock,
                               mock_logbook_title_string_patches: MagicMock,
                               stk_mode: SkyTempleKeyHintMode,
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

    # Run
    result = patcher_file._create_string_patches(HintConfiguration(sky_temple_keys=stk_mode),
                                                 game,
                                                 all_patches,
                                                 player_config,
                                                 rng,
                                                 )

    # Assert
    expected_result = ["item", "hints"]
    mock_item_create_hints.assert_called_once_with(all_patches, player_config, game.world_list, rng)
    mock_logbook_title_string_patches.assert_called_once_with()

    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        mock_stk_hide_hints.assert_called_once_with()
        mock_stk_create_hints.assert_not_called()
        expected_result.extend(["hide", "hints"])

    else:
        mock_stk_create_hints.assert_called_once_with(all_patches, player_config, game.world_list,
                                                      stk_mode == SkyTempleKeyHintMode.HIDE_AREA)
        mock_stk_hide_hints.assert_not_called()
        expected_result.extend(["show", "hints"])

    assert result == expected_result


def test_create_patcher_file(test_files_dir):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", "seed_a.rdvgame"))
    player_index = 0
    preset = description.permalink.get_preset(player_index)
    cosmetic_patches = CosmeticPatches()

    # Run
    result = patcher_file.create_patcher_file(description, PlayersConfiguration(player_index, {0: "you"}),
                                              cosmetic_patches)

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
        "speed_up_credits": cosmetic_patches.speed_up_credits,
        "disable_hud_popup": cosmetic_patches.disable_hud_popup,
        "pickup_map_icons": cosmetic_patches.pickup_markers,
        "full_map_at_start": cosmetic_patches.open_map,
        "dark_world_varia_suit_damage": preset.configuration.varia_suit_damage,
        "dark_world_dark_suit_damage": preset.configuration.dark_suit_damage,
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": False,
    }
    assert result["default_items"] == {
        "visor": "Combat Visor",
        "beam": "Power Beam",
    }
