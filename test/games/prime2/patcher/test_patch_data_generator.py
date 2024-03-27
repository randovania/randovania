from __future__ import annotations

import dataclasses
import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

import randovania
import randovania.games.prime2.exporter.patch_data_factory
from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter import patch_data_factory
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.hint_configuration import HintConfiguration, SkyTempleKeyHintMode
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.pickup_pool import pickup_creator, pool_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription


@pytest.fixture()
def multiworld_item(echoes_resource_database):
    return echoes_resource_database.get_item(echoes_items.MULTIWORLD_ITEM)


def test_create_starting_popup_empty(echoes_game_patches):
    # Run
    result = patch_data_factory._create_starting_popup(echoes_game_patches)

    # Assert
    assert result == []


def test_create_starting_popup_items(echoes_game_patches, echoes_pickup_database):
    db = echoes_game_patches.game.resource_database

    def create_major(n, included_ammo=()):
        return pickup_creator.create_standard_pickup(
            echoes_pickup_database.get_pickup_with_name(n),
            StandardPickupState(included_ammo=included_ammo),
            db,
            None,
            False,
        )

    missile = pickup_creator.create_ammo_pickup(
        echoes_pickup_database.get_pickup_with_name("Missile Expansion"), [5], False, db
    )
    tank = create_major("Energy Tank")

    starting_pickups = [
        missile,
        missile,
        missile,
        tank,
        tank,
        tank,
        create_major("Dark Beam", (50,)),
        create_major("Screw Attack"),
    ]
    patches = echoes_game_patches.assign_extra_starting_pickups(starting_pickups)

    # Run
    result = patch_data_factory._create_starting_popup(patches)

    # Assert
    assert result == ["Extra starting items:", "Dark Beam, 3 Energy Tank, 3 Missile Expansions, Screw Attack"]


def test_adjust_model_name(randomizer_data):
    # Setup
    patcher_data = {
        "pickups": [
            {
                "model": {"game": "prime2", "name": "DarkVisor"},
                "original_model": {"game": "prime2", "name": "DarkVisor"},
            },
            {
                "model": {"game": "prime2", "name": "SkyTempleKey"},
                "original_model": {"game": "prime2", "name": "SkyTempleKey"},
            },
            {
                "model": {"game": "prime2", "name": "MissileExpansion"},
                "original_model": {"game": "prime2", "name": "MissileExpansion"},
            },
            {
                "model": {"game": "prime1", "name": "BoostBall"},
                "original_model": {"game": "prime1", "name": "Boost Ball"},
            },
            {
                "model": {"game": "prime1", "name": "EnergyTransferModule"},
                "original_model": {"game": "prime1", "name": "Plasma Beam"},
            },
        ]
    }

    # Run
    patch_data_factory.adjust_model_name(patcher_data, randomizer_data)

    # Assert
    assert patcher_data == {
        "pickups": [
            {"model_index": 11, "sound_index": 0, "jingle_index": 1},
            {"model_index": 38, "sound_index": 1, "jingle_index": 2},
            {"model_index": 22, "sound_index": 0, "jingle_index": 0},
            {"model_index": 18, "sound_index": 0, "jingle_index": 1},
            {"model_index": 30, "sound_index": 0, "jingle_index": 1},
        ]
    }


def test_add_header_data_to_result():
    # Setup
    description = MagicMock()
    description.shareable_word_hash = "<shareable_word_hash>"
    description.shareable_hash = "<shareable_hash>"
    expected = {
        "permalink": "-permalink-",
        "seed_hash": "- <shareable_word_hash> (<shareable_hash>)",
        "randovania_version": randovania.VERSION,
        "shareable_hash": "<shareable_hash>",
        "shareable_word_hash": "<shareable_word_hash>",
    }
    result = {}

    # Run
    patch_data_factory._add_header_data_to_result(description, result)

    # Assert
    assert json.loads(json.dumps(result)) == expected


def test_create_spawn_point_field(echoes_game_description, echoes_pickup_database, empty_patches):
    # Setup
    resource_db = echoes_game_description.resource_database

    morph = pickup_creator.create_standard_pickup(
        echoes_pickup_database.get_pickup_with_name("Morph Ball"), StandardPickupState(), resource_db, None, False
    )

    loc = NodeIdentifier.create("Temple Grounds", "Hive Chamber B", "Door to Hive Storage")
    patches = empty_patches.assign_starting_location(loc).assign_extra_starting_pickups([morph])

    capacities = [
        {"amount": 1 if item.short_name == "MorphBall" else 0, "index": item.extra["item_id"]}
        for item in resource_db.item
        if item.extra["item_id"] < 1000
    ]

    # Run
    result = patch_data_factory._create_spawn_point_field(patches, echoes_game_description)

    # Assert
    assert result == {
        "location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 494654382,
        },
        "amount": capacities,
        "capacity": capacities,
    }


def test_create_elevators_field_no_elevator(empty_patches, echoes_game_description):
    with pytest.raises(InvalidConfiguration, match="Invalid elevator count. Expected 22, got 0."):
        patch_data_factory._create_elevators_field(
            empty_patches, echoes_game_description, echoes_game_description.dock_weakness_database.find_type("elevator")
        )


@pytest.mark.parametrize("vanilla_gateway", [False, True])
def test_create_elevators_field_elevators_for_a_seed(
    vanilla_gateway: bool, echoes_game_description, echoes_game_patches
):
    # Setup
    wl = echoes_game_description.region_list
    elevator_connection: list[tuple[DockNode, Node]] = []

    def add(region: str, area: str, node: str, target_world: str, target_area: str, target_node: str):
        elevator_connection.append(
            (
                wl.typed_node_by_identifier(NodeIdentifier.create(region, area, node), DockNode),
                wl.node_by_identifier(NodeIdentifier.create(target_world, target_area, target_node)),
            )
        )

    add(
        "Temple Grounds",
        "Temple Transport C",
        "Elevator to Great Temple",
        "Sanctuary Fortress",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
    )
    add(
        "Temple Grounds",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
        "Torvus Bog",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
    )

    if not vanilla_gateway:
        add(
            "Temple Grounds",
            "Sky Temple Gateway",
            "Elevator to Great Temple",
            "Great Temple",
            "Sanctum",
            "Door to Sanctum Access",
        )

    patches = echoes_game_patches.assign_dock_connections(elevator_connection)

    # Run
    result = patch_data_factory._create_elevators_field(
        patches, echoes_game_description, echoes_game_description.dock_weakness_database.find_type("elevator")
    )

    # Assert
    expected = [
        {
            "instance_id": 589851,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
            "room_name": "Transport to Sanctuary Spider side",
        },
        {
            "instance_id": 1572998,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
            "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
            "room_name": "Transport to Torvus Temple Access",
        },
        {
            "instance_id": 1966093,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
            "target_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
            "room_name": "Transport to Torvus Entrance",
        },
        {
            "instance_id": 2097251,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
            "target_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
            "room_name": "Transport to Temple Transport Violet",
        },
        {
            "instance_id": 136970379,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 2278776548},
            "target_location": {
                "world_asset_id": 2252328306,
                "area_asset_id": 2068511343 if vanilla_gateway else 3619928121,
            },
            "room_name": "Sky Temple Gateway" if vanilla_gateway else "Transport to Sanctum",
        },
        {
            "instance_id": 3342446,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
            "room_name": "Transport to Sanctuary Entrance",
        },
        {
            "instance_id": 3538975,
            "origin_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
            "target_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
            "room_name": "Transport to Temple Transport Emerald",
        },
        {
            "instance_id": 152,
            "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 408633584},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1345979968},
            "room_name": "Transport to Sanctuary Quadrant",
        },
        {
            "instance_id": 393260,
            "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2556480432},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2918020398},
            "room_name": "Transport to Torvus Quadrant",
        },
        {
            "instance_id": 524321,
            "origin_location": {"world_asset_id": 2252328306, "area_asset_id": 2399252740},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1287880522},
            "room_name": "Transport to Agon Quadrant",
        },
        {
            "instance_id": 589949,
            "origin_location": {"area_asset_id": 2068511343, "world_asset_id": 2252328306},
            "target_location": {"area_asset_id": 2278776548, "world_asset_id": 1006255871},
            "room_name": "Sky Temple Energy Controller",
        },
        {
            "instance_id": 122,
            "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 1473133138},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 1660916974},
            "room_name": "Transport to Agon Gate",
        },
        {
            "instance_id": 1245307,
            "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
            "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
            "room_name": "Transport to Torvus Temple Access",
        },
        {
            "instance_id": 2949235,
            "origin_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
            "room_name": "Transport to Sanctuary Spider side",
        },
        {
            "instance_id": 129,
            "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 1868895730},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 2889020216},
            "room_name": "Transport to Torvus Gate",
        },
        {
            "instance_id": 2162826,
            "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3479543630},
            "target_location": {"world_asset_id": 1119434212, "area_asset_id": 2806956034},
            "room_name": "Transport to Agon Portal Access",
        },
        {
            "instance_id": 4522032,
            "origin_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
            "room_name": "Transport to Sanctuary Vault side",
        },
        {
            "instance_id": 38,
            "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3528156989},
            "target_location": {"world_asset_id": 1006255871, "area_asset_id": 3455543403},
            "room_name": "Transport to Sanctuary Gate",
        },
        {
            "instance_id": 1245332,
            "origin_location": {"world_asset_id": 464164546, "area_asset_id": 900285955},
            "target_location": {"world_asset_id": 1119434212, "area_asset_id": 3331021649},
            "room_name": "Transport to Agon Temple Access",
        },
        {
            "instance_id": 1638535,
            "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3145160350},
            "target_location": {"world_asset_id": 1039999561, "area_asset_id": 3205424168},
            "room_name": "Transport to Lower Torvus Access",
        },
        {
            "instance_id": 204865660,
            "origin_location": {"world_asset_id": 464164546, "area_asset_id": 3136899603},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 1564082177},
            "room_name": "Aerie Transport Station",
        },
        {
            "instance_id": 4260106,
            "origin_location": {"world_asset_id": 464164546, "area_asset_id": 1564082177},
            "target_location": {"world_asset_id": 464164546, "area_asset_id": 3136899603},
            "room_name": "Aerie",
        },
    ]
    assert result == expected


def test_create_translator_gates_field(echoes_game_description):
    # Setup
    gate_assignment = {
        "Temple Grounds/Meeting Grounds/Translator Gate": "violet",
        "Temple Grounds/Industrial Site/Translator Gate": "amber",
        "Temple Grounds/Path of Eyes/Translator Gate": "violet",
    }

    # Run
    result = patch_data_factory._create_translator_gates_field(echoes_game_description, gate_assignment)

    # Assert
    assert result == [
        {"gate_index": 1, "translator_index": 97},
        {"gate_index": 3, "translator_index": 98},
        {"gate_index": 4, "translator_index": 97},
    ]


@pytest.mark.parametrize("teleporters", [TeleporterShuffleMode.VANILLA, TeleporterShuffleMode.TWO_WAY_RANDOMIZED])
def test_apply_translator_gate_patches(teleporters):
    # Setup
    target = {}

    # Run
    patch_data_factory._apply_translator_gate_patches(target, teleporters)

    # Assert
    assert target == {
        "always_up_gfmc_compound": True,
        "always_up_torvus_temple": True,
        "always_up_great_temple": teleporters != TeleporterShuffleMode.VANILLA,
    }


def test_get_single_hud_text_locked_pbs():
    # Run
    result = pickup_exporter._get_single_hud_text(
        "Locked Power Bomb Expansion", patch_data_factory._simplified_memo_data(), ()
    )

    # Assert
    assert result == "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."


def test_pickup_data_for_seeker_launcher(echoes_pickup_database, multiworld_item, echoes_resource_database):
    # Setup
    state = StandardPickupState(
        include_copy_in_original_location=False,
        num_shuffled_pickups=0,
        num_included_in_starting_pickups=0,
        included_ammo=(5,),
    )
    pickup = pickup_creator.create_standard_pickup(
        echoes_pickup_database.standard_pickups["Seeker Launcher"],
        state,
        echoes_resource_database,
        echoes_pickup_database.ammo_pickups["Missile Expansion"],
        True,
    )
    creator = pickup_exporter.PickupExporterSolo(
        patch_data_factory._simplified_memo_data(), RandovaniaGame.METROID_PRIME_ECHOES
    )

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, multiworld_item, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Seeker Launcher.",
        "model": {"game": "prime2", "name": "SeekerLauncher"},
        "original_model": {"game": "prime2", "name": "SeekerLauncher"},
        "hud_text": [
            "Seeker Launcher acquired, but the Missile Launcher is required to use it.",
            "Seeker Launcher acquired!",
        ],
        "resources": [
            {"amount": 5, "index": 71},
            {"amount": 1, "index": 47},
            {"amount": 1, "index": 26},
            {"amount": 1, "index": 74},
        ],
        "conditional_resources": [
            {
                "item": 73,
                "resources": [
                    {"amount": 5, "index": 44},
                    {"amount": 1, "index": 47},
                    {"amount": 1, "index": 26},
                    {"amount": 1, "index": 74},
                ],
            }
        ],
        "convert": [],
    }


@pytest.mark.parametrize("simplified", [False, True])
def test_pickup_data_for_pb_expansion_locked(
    simplified, echoes_pickup_database, multiworld_item, echoes_resource_database
):
    # Setup
    pickup = pickup_creator.create_ammo_pickup(
        echoes_pickup_database.ammo_pickups["Power Bomb Expansion"],
        [2],
        True,
        echoes_resource_database,
    )
    if simplified:
        memo = patch_data_factory._simplified_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired, but the main Power Bomb is required to use it.",
            "Power Bomb Expansion acquired!",
        ]
    else:
        memo = patch_data_factory.default_prime2_memo_data()
        hud_text = [
            "Power Bomb Expansion acquired! \n"
            "Without the main Power Bomb item, you are still unable to release Power Bombs.",
            "Power Bomb Expansion acquired! \nMaximum Power Bomb carrying capacity increased by 2.",
        ]

    creator = pickup_exporter.PickupExporterSolo(memo, RandovaniaGame.METROID_PRIME_ECHOES)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, multiworld_item, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage.",
        "model": {"game": "prime2", "name": "PowerBombExpansion"},
        "original_model": {"game": "prime2", "name": "PowerBombExpansion"},
        "hud_text": hud_text,
        "resources": [{"amount": 2, "index": 72}, {"amount": 1, "index": 47}, {"amount": 1, "index": 74}],
        "conditional_resources": [
            {
                "item": 43,
                "resources": [{"amount": 2, "index": 43}, {"amount": 1, "index": 47}, {"amount": 1, "index": 74}],
            }
        ],
        "convert": [],
    }


def test_pickup_data_for_pb_expansion_unlocked(echoes_pickup_database, multiworld_item, echoes_resource_database):
    # Setup
    pickup = pickup_creator.create_ammo_pickup(
        echoes_pickup_database.ammo_pickups["Power Bomb Expansion"],
        [2],
        False,
        echoes_resource_database,
    )
    creator = pickup_exporter.PickupExporterSolo(
        patch_data_factory._simplified_memo_data(), RandovaniaGame.METROID_PRIME_ECHOES
    )

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = patch_data_factory.echoes_pickup_details_to_patcher(details, multiworld_item, MagicMock())

    # Assert
    assert result == {
        "pickup_index": 0,
        "scan": "Power Bomb Expansion. Provides 2 Power Bombs and 1 Item Percentage.",
        "model": {"game": "prime2", "name": "PowerBombExpansion"},
        "original_model": {"game": "prime2", "name": "PowerBombExpansion"},
        "hud_text": ["Power Bomb Expansion acquired!"],
        "resources": [{"amount": 2, "index": 43}, {"amount": 1, "index": 47}, {"amount": 1, "index": 74}],
        "conditional_resources": [],
        "convert": [],
    }


@pytest.mark.parametrize("disable_hud_popup", [False, True])
def test_create_pickup_all_from_pool(echoes_game_description, default_echoes_configuration, disable_hud_popup: bool):
    item_pool = pool_creator.calculate_pool_results(default_echoes_configuration, echoes_game_description)
    index = PickupIndex(0)
    if disable_hud_popup:
        memo_data = patch_data_factory._simplified_memo_data()
    else:
        memo_data = patch_data_factory.default_prime2_memo_data()
    creator = pickup_exporter.PickupExporterSolo(memo_data, RandovaniaGame.METROID_PRIME_ECHOES)

    for item in item_pool.to_place:
        data = creator.export(index, PickupTarget(item, 0), item, PickupModelStyle.ALL_VISIBLE)
        for hud_text in data.collection_text:
            assert not hud_text.startswith("Locked")


def test_run_validated_hud_text(multiworld_item):
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    details = pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        name="Energy Transfer Module",
        description="scan",
        collection_text=["Energy Transfer Module acquired!"],
        conditional_resources=[
            ConditionalResources(None, None, ()),
        ],
        conversion=[],
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        original_model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        other_player=False,
        original_pickup=None,
    )

    # Run
    data = patch_data_factory.echoes_pickup_details_to_patcher(details, multiworld_item, rng)

    # Assert
    assert data["hud_text"] == ["Run validated!"]


@pytest.mark.parametrize("stk_mode", SkyTempleKeyHintMode)
def test_create_string_patches(
    stk_mode: SkyTempleKeyHintMode,
    mocker,
):
    # Setup
    game: GameDescription = MagicMock()
    all_patches = MagicMock()
    rng = MagicMock()
    player_config = PlayersConfiguration(0, {0: "you"})

    mock_item_create_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.create_patches_hints",
        autospec=True,
        return_value=["item", "hints"],
    )
    mock_stk_create_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.create_stk_hints",
        autospec=True,
        return_value=["show", "hints"],
    )
    mock_stk_hide_hints: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.hints.hide_stk_hints",
        autospec=True,
        return_value=["hide", "hints"],
    )
    mock_logbook_title_string_patches: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.patch_data_factory._logbook_title_string_patches",
        autospec=True,
        return_values=[],
    )

    mock_akul_testament: MagicMock = mocker.patch(
        "randovania.games.prime2.exporter.patch_data_factory._akul_testament_string_patch",
        autospec=True,
    )
    mock_akul_testament.return_values = []
    namer = MagicMock()

    # Run
    result = patch_data_factory._create_string_patches(
        HintConfiguration(sky_temple_keys=stk_mode),
        False,
        game,
        all_patches,
        namer,
        player_config,
        rng,
        None,
    )

    # Assert
    expected_result = ["item", "hints"]
    mock_item_create_hints.assert_called_once_with(all_patches, player_config, game.region_list, namer, rng)
    mock_logbook_title_string_patches.assert_called_once_with()
    mock_akul_testament.assert_called_once_with(namer)

    if stk_mode == SkyTempleKeyHintMode.DISABLED:
        mock_stk_hide_hints.assert_called_once_with(namer)
        mock_stk_create_hints.assert_not_called()
        expected_result.extend(["hide", "hints"])

    else:
        mock_stk_create_hints.assert_called_once_with(
            all_patches, player_config, game.resource_database, namer, stk_mode == SkyTempleKeyHintMode.HIDE_AREA
        )
        mock_stk_hide_hints.assert_not_called()
        expected_result.extend(["show", "hints"])

    assert result == expected_result


@pytest.mark.usefixtures("_mock_seed_hash")
@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "use_new_patcher"),
    [
        ("seed_a.rdvgame", "seed_a_old_patcher.json", False),
        ("seed_a.rdvgame", "seed_a_new_patcher.json", True),
        ("prime2_no_pbs.rdvgame", "prime2_no_pbs_old_patcher.json", False),
        ("prime2_no_pbs.rdvgame", "prime2_no_pbs_new_patcher.json", True),
    ],
)
def test_generate_patcher_data(
    test_files_dir, rdvgame_filename, expected_results_filename, use_new_patcher, monkeypatch, mocker
):
    # Setup
    description = LayoutDescription.from_file(test_files_dir.joinpath("log_files", rdvgame_filename))
    player_index = 0
    preset = description.get_preset(player_index)
    cosmetic_patches = EchoesCosmeticPatches()
    assert isinstance(preset.configuration, EchoesConfiguration)
    configuration = dataclasses.replace(preset.configuration, use_new_patcher=use_new_patcher)
    description.generator_parameters.presets[player_index] = dataclasses.replace(preset, configuration=configuration)
    monkeypatch.setattr(randovania, "VERSION", "Test Version")

    # Run
    factory = patch_data_factory.EchoesPatchDataFactory(
        description, PlayersConfiguration(player_index, {0: "you"}), cosmetic_patches
    )
    result = factory.create_data()

    # Assert
    expected_results_path = test_files_dir.joinpath("patcher_data", "prime2", expected_results_filename)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, result)

    expected_result = json_lib.read_path(expected_results_path)

    assert result == expected_result
