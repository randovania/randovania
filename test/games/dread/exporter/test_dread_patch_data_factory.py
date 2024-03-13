from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

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
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.layout_description import LayoutDescription

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize("locked", [False, True])
def test_pickup_data_for_pb_expansion(
    locked: bool, dread_game_description: GameDescription, preset_manager: PresetManager
) -> None:
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
        (
            [
                {"item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 2},
            ]
            if locked
            else [
                {"item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 2},
                {"item_id": "ITEM_WEAPON_POWER_BOMB", "quantity": 1},
            ]
        )
    ]


@pytest.mark.parametrize("locked", [False, True])
def test_pickup_data_for_main_pb(
    locked: bool, dread_game_description: GameDescription, preset_manager: PresetManager
) -> None:
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    # Setup
    pickup = pickup_creator.create_standard_pickup(
        pickup_database.standard_pickups["Power Bomb"],
        StandardPickupState(included_ammo=(3,)),
        resource_database=resource_db,
        ammo=pickup_database.ammo_pickups["Power Bomb Tank"],
        ammo_requires_main_item=locked,
    )

    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = get_resources_for_details(details.original_pickup, details.conditional_resources, details.other_player)

    # Assert
    assert result == [
        [
            {"item_id": "ITEM_WEAPON_POWER_BOMB", "quantity": 1},
            {"item_id": "ITEM_WEAPON_POWER_BOMB_MAX", "quantity": 3},
        ]
    ]


def test_pickup_data_for_recolored_missiles(
    dread_game_description: GameDescription, preset_manager: PresetManager
) -> None:
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    description = MagicMock(spec=LayoutDescription)
    description.all_patches = {0: MagicMock()}
    description.get_preset.return_value = preset
    description.get_seed_for_player.return_value = 1000
    cosmetics = DreadCosmeticPatches(missile_cosmetic=DreadMissileCosmeticType.PRIDE)

    # Setup
    pickup = pickup_creator.create_ammo_pickup(
        pickup_database.ammo_pickups["Missile Tank"], (2,), False, resource_database=resource_db
    )

    factory = DreadPatchDataFactory(description, PlayersConfiguration(0, {0: "Dread"}), cosmetics)
    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = factory._pickup_detail_for_target(details)

    # Assert
    assert result == {
        "pickup_type": "actor",
        "caption": "Missile Tank acquired.\nMissile capacity increased by 2.",
        "resources": [[{"item_id": "ITEM_WEAPON_MISSILE_MAX", "quantity": 2}]],
        "pickup_actor": {"scenario": "s010_cave", "layer": "default", "actor": "ItemSphere_ChargeBeam"},
        "model": ["item_missiletank_green"],
        "map_icon": {
            "icon_id": "item_missiletank",
            "original_actor": {"actor": "powerup_chargebeam", "layer": "default", "scenario": "s010_cave"},
        },
    }


def test_pickup_data_for_a_major(dread_game_description: GameDescription, preset_manager: PresetManager) -> None:
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    resource_db = dread_game_description.resource_database

    preset = preset_manager.default_preset_for_game(RandovaniaGame.METROID_DREAD).get_preset()
    description = MagicMock(spec=LayoutDescription)
    description.all_patches = {0: MagicMock()}
    description.get_preset.return_value = preset
    description.get_seed_for_player.return_value = 1000

    # Setup
    pickup = pickup_creator.create_standard_pickup(
        pickup_database.standard_pickups["Speed Booster"],
        StandardPickupState(),
        resource_database=resource_db,
        ammo=None,
        ammo_requires_main_item=False,
    )

    factory = DreadPatchDataFactory(description, PlayersConfiguration(0, {0: "Dread"}), MagicMock())
    creator = pickup_exporter.PickupExporterSolo(DreadAcquiredMemo.with_expansion_text(), RandovaniaGame.METROID_DREAD)

    # Run
    details = creator.export(PickupIndex(0), PickupTarget(pickup, 0), pickup, PickupModelStyle.ALL_VISIBLE)
    result = factory._pickup_detail_for_target(details)

    # Assert
    assert result == {
        "pickup_type": "actor",
        "caption": "Speed Booster acquired.",
        "resources": [[{"item_id": "ITEM_SPEED_BOOSTER", "quantity": 1}]],
        "pickup_actor": {"scenario": "s010_cave", "layer": "default", "actor": "ItemSphere_ChargeBeam"},
        "model": ["powerup_speedbooster"],
        "map_icon": {
            "icon_id": "powerup_speedbooster",
            "original_actor": {"actor": "powerup_chargebeam", "layer": "default", "scenario": "s010_cave"},
        },
    }
