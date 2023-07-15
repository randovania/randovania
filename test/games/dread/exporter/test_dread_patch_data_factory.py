from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, PropertyMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.dread.exporter.patch_data_factory import (
    DreadAcquiredMemo,
    DreadPatchDataFactory,
    get_resources_for_details,
)
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches, DreadMissileCosmeticType
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.ammo_pickup_state import AmmoPickupState
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.layout.preset import Preset


@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "starter_preset.json", 1),                             # starter preset
        ("crazy_settings.rdvgame", "crazy_settings.json", 1),                             # crazy settings
        ("dread_dread_multiworld.rdvgame", "dread_dread_multiworld_expected.json", 2),    # dread-dread multi
        ("dread_prime1_multiworld.rdvgame", "dread_prime1_multiworld_expected.json", 2),  # dread-prime1 multi
    ]
)
def test_create_patch_data(test_files_dir, rdvgame_filename,
                            expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "dread", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = DreadCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    # Run
    data = DreadPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "dread", expected_results_filename)
    expected_data = json_lib.read_path(expected_results_path)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, data); assert False

    assert data == expected_data


def _preset_with_locked_pb(preset: Preset, locked: bool):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    preset = dataclasses.replace(
        preset,
        configuration=dataclasses.replace(
            preset.configuration,
            ammo_configuration=preset.configuration.ammo_pickup_configuration.replace_state_for_ammo(
                pickup_database.ammo_pickups["Power Bomb Tank"],
                AmmoPickupState(requires_main_item=locked),
            )
        )
    )
    return preset


@pytest.mark.parametrize("locked", [False, True])
def test_pickup_data_for_pb_expansion(locked, dread_game_description, preset_manager):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    # Setup
    pickup = pickup_creator.create_ammo_pickup(
        pickup_database.ammo_pickups["Power Bomb Tank"],
        [2],
        locked,
        resource_db,
    )

    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = get_resources_for_details(details.original_pickup, details.conditional_resources, details.other_player)

    # Assert
    assert result == [
        [
            { "item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 2 },
        ]
        if locked else
        [
            { "item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 2 },
            { "item_id": "ITEM_WEAPON_POWER_BOMB", "quantity": 1 },
        ]
    ]


@pytest.mark.parametrize("locked", [False, True])
def test_pickup_data_for_main_pb(locked, dread_game_description, preset_manager):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    # Setup
    pickup = pickup_creator.create_standard_pickup(pickup_database.standard_pickups["Power Bomb"],
                                                   StandardPickupState(included_ammo=(3,)),
                                                   resource_database=resource_db,
                                                   ammo=pickup_database.ammo_pickups["Power Bomb Tank"],
                                                   ammo_requires_main_item=locked)

    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = get_resources_for_details(details.original_pickup, details.conditional_resources, details.other_player)

    # Assert
    assert result == [
        [
            { "item_id": "ITEM_WEAPON_POWER_BOMB", "quantity": 1 },
            { "item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 3 },
        ]
    ]

def test_pickup_data_for_recolored_missiles(dread_game_description, preset_manager):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    description = MagicMock(spec=LayoutDescription)
    description.all_patches = {0: MagicMock()}
    description.get_preset.return_value = preset
    description.get_seed_for_player.return_value = 1000
    cosmetics = DreadCosmeticPatches(missile_cosmetic=DreadMissileCosmeticType.PRIDE)

    # Setup
    pickup = pickup_creator.create_ammo_pickup(pickup_database.ammo_pickups["Missile Tank"],
                                               (2,),
                                               False,
                                               resource_database=resource_db)

    factory = DreadPatchDataFactory(description, PlayersConfiguration(0, {0: "Dread"}), cosmetics)
    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = factory._pickup_detail_for_target(details)

    # Assert
    assert result == {
        "pickup_type": "actor",
        "caption": "Missile Tank acquired.\nMissile capacity increased by 2.",
        "resources": [
            [
                {
                    "item_id": "ITEM_WEAPON_MISSILE_MAX",
                    "quantity": 2
                }
            ]
        ],
        "pickup_actor": {
            "scenario": "s010_cave",
            "layer": "default",
            "actor": "ItemSphere_ChargeBeam"
        },
        "model": [
            "item_missiletank_green"
        ],
        "map_icon": {
            "icon_id": "item_missiletank",
            'original_actor': {'actor': 'powerup_chargebeam',
                               'layer': 'default',
                               'scenario': 's010_cave'}
        }
    }

def test_pickup_data_for_a_major(dread_game_description, preset_manager):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    description = MagicMock(spec=LayoutDescription)
    description.all_patches = {0: MagicMock()}
    description.get_preset.return_value = preset
    description.get_seed_for_player.return_value = 1000

    # Setup
    pickup = pickup_creator.create_standard_pickup(pickup_database.standard_pickups["Speed Booster"],
                                                   StandardPickupState(), resource_database=resource_db, ammo=None,
                                                   ammo_requires_main_item=False)

    factory = DreadPatchDataFactory(description, PlayersConfiguration(0, {0: "Dread"}), MagicMock())
    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = factory._pickup_detail_for_target(details)

    # Assert
    assert result == {
        "pickup_type": "actor",
        "caption": "Speed Booster acquired.",
        "resources": [
            [
                {
                    "item_id": "ITEM_SPEED_BOOSTER",
                    "quantity": 1
                }
            ]
        ],
        "pickup_actor": {
            "scenario": "s010_cave",
            "layer": "default",
            "actor": "ItemSphere_ChargeBeam"
        },
        "model": [
            "powerup_speedbooster"
        ],
        "map_icon": {
            "icon_id": "powerup_speedbooster",
            'original_actor': {'actor': 'powerup_chargebeam',
                               'layer': 'default',
                               'scenario': 's010_cave'}
        }
    }


@pytest.fixture()
def _setup_and_teardown_for_wrong_custom_spawn():
    # modify the default start to have no collision_camera (asset_id) and no vanilla
    # actor name for a start point
    game_desc = default_database.game_description_for(RandovaniaGame.METROID_DREAD)
    region = game_desc.region_list.region_with_name("Artaria")
    area = region.area_by_name("Intro Room")
    node = area.node_with_name("Start Point")
    modified_node = dataclasses.replace(node, extra={})
    area.nodes.remove(node)
    area.nodes.append(modified_node)
    asset_id = area.extra["asset_id"]
    del area.extra["asset_id"]
    yield
    area.nodes.remove(modified_node)
    area.nodes.append(node)
    area.extra["asset_id"] = asset_id


@pytest.mark.usefixtures("_setup_and_teardown_for_wrong_custom_spawn")
def test_create_patch_with_wrong_custom_spawn(test_files_dir, mocker):
    # test for a not createable spawn point
    file = test_files_dir.joinpath("log_files", "dread", "starter_preset.rdvgame")
    description = LayoutDescription.from_file(file)
    players_config = PlayersConfiguration(0, {0: "Dread"})
    cosmetic_patches = DreadCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    patcher = DreadPatchDataFactory(description, players_config, cosmetic_patches)
    with pytest.raises(KeyError,
                       match="Artaria/Intro Room/Start Point has neither a start_point_actor_name nor the "
                             "area has a collision_camera_name for a custom start point"):
        patcher.create_data()


@pytest.fixture()
def _setup_and_teardown_for_custom_spawn():
    # modify a node to be a valid start point without a vanilla spawn
    game_desc = default_database.game_description_for(RandovaniaGame.METROID_DREAD)
    region = game_desc.region_list.region_with_name("Artaria")
    area = region.area_by_name("Charge Tutorial")
    node = area.node_with_name("Start Point")
    modified_node = dataclasses.replace(node, valid_starting_location=True)
    area.nodes.remove(node)
    area.nodes.append(modified_node)
    yield
    area.nodes.remove(modified_node)
    area.nodes.append(node)


@pytest.mark.usefixtures("_setup_and_teardown_for_custom_spawn")
def test_create_patch_with_custom_spawn(test_files_dir, mocker):
    # test for custom spawn point referenced by starting location and teleporters
    file = test_files_dir.joinpath("log_files", "dread", "custom_start.rdvgame")
    description = LayoutDescription.from_file(file)
    players_config = PlayersConfiguration(0, {0: "Dread"})
    cosmetic_patches = DreadCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    data = DreadPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_data = test_files_dir.read_json("patcher_data", "dread", "custom_start.json")

    # Update the file
    # json_lib.write_path(test_files_dir.joinpath("patcher_data", "dread", "custom_start.json"), data); assert False

    assert data == expected_data
