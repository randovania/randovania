from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime1.exporter import game_exporter
from randovania.games.prime1.exporter.patch_data_factory import (
    _shorten_word_hash,
    _starting_items_for,
    prime1_pickup_details_to_patcher,
)
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.standard_pickup_configuration import StandardPickupState


@pytest.mark.parametrize("is_for_remote_player", [False, True])
def test_prime1_pickup_details_to_patcher_shiny_missile(prime1_resource_database, is_for_remote_player: bool):
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    detail = pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(15),
        name="Your Missile Expansion",
        description="Provides 5 Missiles",
        collection_text=["Missile Expansion acquired!"],
        conditional_resources=[
            ConditionalResources(
                None,
                None,
                ((prime1_resource_database.get_item_by_display_name("Missile"), 6),),
            )
        ],
        conversion=[],
        model=PickupModel(RandovaniaGame.METROID_PRIME, "Missile"),
        original_model=PickupModel(RandovaniaGame.METROID_PRIME, "Missile"),
        is_for_remote_player=is_for_remote_player,
        original_pickup=None,
    )
    if is_for_remote_player:
        pickup_type = "Unknown Item 1"
        amount = 16
        shiny_stuff = {
            "model": {"game": "prime1", "name": "Missile"},
            "original_model": {"game": "prime1", "name": "Missile"},
            "scanText": "Your Missile Expansion. Provides 5 Missiles",
            "hudmemoText": "Missile Expansion acquired!",
        }
    else:
        pickup_type = "Missile"
        amount = 6
        shiny_stuff = {
            "model": {"game": "prime1", "name": "Shiny Missile"},
            "original_model": {"game": "prime1", "name": "Shiny Missile"},
            "scanText": "Your Shiny Missile Expansion. Provides 5 Missiles",
            "hudmemoText": "Shiny Missile Expansion acquired!",
        }

    # Run
    result = prime1_pickup_details_to_patcher(detail, False, True, rng)

    # Assert
    assert result == {
        "type": pickup_type,
        "currIncrease": amount,
        "maxIncrease": amount,
        "respawn": False,
        "showIcon": True,
        **shiny_stuff,
    }


@pytest.mark.parametrize(
    "case_name",
    [
        "prime1_and_2_multi",
        "prime1_crazy_seed",
        "prime1_crazy_seed_one_way_door",
    ],
)
@pytest.mark.parametrize(
    "external_assets",
    [False, True],
)
def test_adjust_model_names(test_files_dir, case_name: str, external_assets: bool) -> None:
    assets_meta = {"items": []}
    data = test_files_dir.read_json("patcher_data", "prime1", case_name, "world_1.json")

    game_exporter.adjust_model_names(data, assets_meta, external_assets)


@pytest.mark.parametrize(
    ("word_hash", "expected"),
    [
        ("Grove Ice Bomb", "Grove Ice Bomb"),
        ("Wavebuster Thardus Grove", "Wavebuster Thardus Grove"),
        ("Wavebuster Thardus", "Wavebuster Thardus"),
        ("Supercalifragilistic", "Supercalifragilistic"),
        ("Metroid Prime Chozo Artifact Temple", "Met. Pri. Cho. Art. Tem."),
        ("A B C D E F G H I J", "A B C D E F G H I J"),
        ("A B C D E F G H I J K L M", "A B C D E F G H I J K L"),
        ("Warrior Worm Workstation", "Warrior Worm Workstation"),
        ("Wavebuster Thardus Sunchamber", "Wavebus. Thardus Suncha."),
        ("Exoskeleton Shorelines Ghost", "Exoskele. Shoreli. Ghost"),
    ],
)
def test_shorten_word_hash(word_hash: str, expected: str) -> None:
    assert _shorten_word_hash(word_hash) == expected
    assert len(expected) <= 24


def _details_for_prime1_pickup(pickup):
    conditional_resources = pickup_exporter._conditional_resources_for_pickup(pickup)

    memo_data = pickup_exporter.GenericAcquiredMemo()
    memo_data["Locked Missile Expansion"] = (
        "Missile Expansion acquired, but the Missile Launcher is required to use it."
    )
    memo_data["Locked Power Bomb Expansion"] = (
        "Power Bomb Expansion acquired, but the main Power Bomb is required to use it."
    )

    return pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(0),
        name=pickup.name,
        description="",
        collection_text=pickup_exporter._get_all_hud_text(conditional_resources, memo_data),
        conditional_resources=conditional_resources,
        conversion=list(pickup.convert_resources),
        model=pickup.model,
        original_model=pickup.model,
        is_for_remote_player=False,
        original_pickup=pickup,
    )


@pytest.mark.parametrize(
    ("pickup_name", "ammo_name", "included_ammo", "expected_type"),
    [
        ("Missile Launcher", "Missile Expansion", 5, "Missile Launcher"),
        ("Power Bomb", "Power Bomb Expansion", 4, "Main Power Bomb"),
    ],
)
def test_prime1_required_main_pickup_to_patcher(
    prime1_resource_database,
    pickup_name: str,
    ammo_name: str,
    included_ammo: int,
    expected_type: str,
):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_PRIME)

    pickup = pickup_creator.create_standard_pickup(
        pickup_database.standard_pickups[pickup_name],
        StandardPickupState(included_ammo=(included_ammo,)),
        prime1_resource_database,
        pickup_database.ammo_pickups[ammo_name],
        True,
    )

    detail = _details_for_prime1_pickup(pickup)
    result = prime1_pickup_details_to_patcher(detail, False, True, MagicMock())

    assert result["type"] == expected_type
    assert result["currIncrease"] == 0
    assert result["maxIncrease"] == included_ammo
    assert "conditionalHudmemo" not in result


@pytest.mark.parametrize(
    ("ammo_name", "amount", "expected_type", "required_item", "missing_text"),
    [
        (
            "Missile Expansion",
            5,
            "Missile",
            "Missile Launcher",
            "Missile Expansion acquired, but the Missile Launcher is required to use it.",
        ),
        (
            "Power Bomb Expansion",
            1,
            "Power Bomb",
            "Main Power Bomb",
            "Power Bomb Expansion acquired, but the main Power Bomb is required to use it.",
        ),
    ],
)
def test_prime1_required_ammo_pickup_to_patcher(
    prime1_resource_database,
    ammo_name: str,
    amount: int,
    expected_type: str,
    required_item: str,
    missing_text: str,
):
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_PRIME)

    pickup = pickup_creator.create_ammo_pickup(
        pickup_database.ammo_pickups[ammo_name],
        (amount,),
        True,
        prime1_resource_database,
    )

    detail = _details_for_prime1_pickup(pickup)
    result = prime1_pickup_details_to_patcher(detail, False, True, MagicMock())

    assert len(detail.conditional_resources) == 2
    assert result["type"] == expected_type
    assert result["currIncrease"] == amount
    assert result["maxIncrease"] == amount
    assert result["hudmemoText"] == f"{ammo_name} acquired!"
    assert result["conditionalHudmemo"] == {
        "requiredItem": required_item,
        "missingText": missing_text,
    }


@pytest.mark.parametrize(
    (
        "missile_requires_main",
        "power_bomb_requires_main",
        "resource_values",
        "expected",
    ),
    [
        (
            False,
            False,
            {},
            {
                "missileLauncher": True,
                "powerBombLauncher": True,
                "missiles": 0,
                "powerBombs": 0,
            },
        ),
        (
            True,
            False,
            {},
            {
                "missileLauncher": False,
                "powerBombLauncher": True,
                "missiles": 0,
                "powerBombs": 0,
            },
        ),
        (
            True,
            False,
            {"MissileLauncher": 1},
            {
                "missileLauncher": True,
                "powerBombLauncher": True,
                "missiles": 0,
                "powerBombs": 0,
            },
        ),
        (
            False,
            True,
            {},
            {
                "missileLauncher": True,
                "powerBombLauncher": False,
                "missiles": 0,
                "powerBombs": 0,
            },
        ),
        (
            False,
            True,
            {"MainPB": 1},
            {
                "missileLauncher": True,
                "powerBombLauncher": True,
                "missiles": 0,
                "powerBombs": 0,
            },
        ),
        (
            True,
            True,
            {
                "LockedMissile": 10,
                "LockedPB": 3,
            },
            {
                "missileLauncher": False,
                "powerBombLauncher": False,
                "missiles": 10,
                "powerBombs": 3,
            },
        ),
        (
            True,
            True,
            {
                "Missile": 5,
                "LockedMissile": 10,
                "PowerBomb": 2,
                "LockedPB": 3,
            },
            {
                "missileLauncher": False,
                "powerBombLauncher": False,
                "missiles": 15,
                "powerBombs": 5,
            },
        ),
    ],
)
def test_prime1_starting_items_required_mains(
    prime1_resource_database,
    missile_requires_main: bool,
    power_bomb_requires_main: bool,
    resource_values: dict[str, int],
    expected: dict[str, bool | int],
):
    values = {prime1_resource_database.get_item(name): value for name, value in resource_values.items()}

    starting_resources = MagicMock()
    starting_resources.__getitem__.side_effect = lambda item: values.get(item, 0)

    result = _starting_items_for(
        prime1_resource_database,
        starting_resources,
        missile_requires_main,
        power_bomb_requires_main,
    )

    for key, value in expected.items():
        assert result[key] == value

    assert result["unlimitedMissiles"] is False
    assert result["unlimitedPowerBombs"] is False
