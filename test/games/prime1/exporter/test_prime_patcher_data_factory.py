from __future__ import annotations

import copy
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, PropertyMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.pickup.pickup_entry import ConditionalResources, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter import game_exporter
from randovania.games.prime1.exporter.patch_data_factory import PrimePatchDataFactory, prime1_pickup_details_to_patcher
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib

if TYPE_CHECKING:
    from pathlib import Path


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


def _test_preset(rdvgame_file: Path, expected_results_file: Path, mocker):
    # Setup
    description = LayoutDescription.from_file(rdvgame_file)
    players_config = PlayersConfiguration(0, {0: "Prime", 1: "Echoes"})
    cosmetic_patches = PrimeCosmeticPatches(
        use_hud_color=True, hud_color=(255, 0, 0), suit_color_rotations=(0, 40, 350, 12), pickup_markers=True
    )

    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash_bytes",
        new_callable=PropertyMock,
        return_value=b"\x00\x00\x00\x00\x00",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
        new_callable=PropertyMock,
        return_value="Words Hash",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash",
        new_callable=PropertyMock,
        return_value="$$$$$",
    )

    # Run
    data = PrimePatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_data = json_lib.read_path(expected_results_file)

    # # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_file, data)

    # Ignore the part of the main menu message which has the randovania version in it
    data["gameConfig"]["mainMenuMessage"] = data["gameConfig"]["mainMenuMessage"].split("\n")[1]
    expected_data["gameConfig"]["mainMenuMessage"] = expected_data["gameConfig"]["mainMenuMessage"].split("\n")[1]

    data["gameConfig"]["resultsString"] = data["gameConfig"]["resultsString"].split("|")[1]
    expected_data["gameConfig"]["resultsString"] = expected_data["gameConfig"]["resultsString"].split("|")[1]

    assert data == expected_data

    assets_meta = {"items": []}
    game_exporter.adjust_model_names(copy.deepcopy(data), assets_meta, False)
    game_exporter.adjust_model_names(copy.deepcopy(data), assets_meta, True)


@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename"),
    [
        ("prime1_and_2_multi.rdvgame", "randomprime_expected_data.json"),  # simple multi
        ("prime1_crazy_seed.rdvgame", "randomprime_expected_data_crazy.json"),  # chaos features
        ("prime1_crazy_seed_one_way_door.rdvgame", "randomprime_expected_data_one_way_door.json"),
        # same as above but 1-way doors
    ],
)
def test_create_patch_data(test_files_dir, rdvgame_filename, expected_results_filename, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", rdvgame_filename)
    expected_results = test_files_dir.joinpath(expected_results_filename)
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
        new_callable=PropertyMock,
        return_value="Words Hash",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash",
        new_callable=PropertyMock,
        return_value="$$$$$",
    )

    _test_preset(rdvgame, expected_results, mocker)
