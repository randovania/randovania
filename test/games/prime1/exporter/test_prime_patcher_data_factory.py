from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter import game_exporter
from randovania.games.prime1.exporter.patch_data_factory import prime1_pickup_details_to_patcher


@pytest.mark.parametrize("other_player", [False, True])
def test_prime1_pickup_details_to_patcher_shiny_missile(prime1_resource_database, other_player: bool):
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
                ((prime1_resource_database.get_item_by_name("Missile"), 6),),
            )
        ],
        conversion=[],
        model=PickupModel(RandovaniaGame.METROID_PRIME, "Missile"),
        original_model=PickupModel(RandovaniaGame.METROID_PRIME, "Missile"),
        other_player=other_player,
        original_pickup=None,
    )
    if other_player:
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
