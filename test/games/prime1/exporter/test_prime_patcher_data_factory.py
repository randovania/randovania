import json
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.resources.pickup_entry import PickupModel, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.exporter.patch_data_factory import prime1_pickup_details_to_patcher, PrimePatchDataFactory
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription


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
        conditional_resources=[ConditionalResources(
            None, None, (
                (prime1_resource_database.get_item_by_name("Missile"), 6),
            ),
        )],
        conversion=[],
        model=PickupModel(RandovaniaGame.METROID_PRIME, "Missile"),
        other_player=other_player,
        original_pickup=None,
    )
    if other_player:
        shiny_stuff = {
            'model': {'game': 'prime1', 'name': 'Missile'},
            'scanText': 'Your Missile Expansion. Provides 5 Missiles',
            'hudmemoText': 'Missile Expansion acquired!',
        }
    else:
        shiny_stuff = {
            'model': {'game': 'prime1', 'name': 'Shiny Missile'},
            'scanText': 'Your Shiny Missile Expansion. Provides 5 Missiles',
            'hudmemoText': 'Shiny Missile Expansion acquired!',
        }

    # Run
    result = prime1_pickup_details_to_patcher(detail, False, True, rng)

    # Assert
    assert result == {
        'type': 'Missile',
        'currIncrease': 6, 'maxIncrease': 6,
        'respawn': False,
        'showIcon': True,
        **shiny_stuff,
    }


def _test_preset(rdvgame_file: Path, expected_results_file: Path, mocker):
    # Setup
    description = LayoutDescription.from_file(rdvgame_file)
    players_config = PlayersConfiguration(0, {0: "Prime", 1: "Echoes"})
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=True, hud_color=(255, 0, 0),
                                            suit_color_rotations=(0, 40, 350, 12), pickup_markers=True,)

    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash_bytes",
                 new_callable=PropertyMock,
                 return_value=b"\x00\x00\x00\x00\x00")

    # Run
    data = PrimePatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    with expected_results_file.open("r") as file:
        expected_data = json.load(file)

    # Uncomment to easily view diff of failed test
    # expected_results_file.write_text(
    #     json.dumps(data, indent=4, separators=(',', ': '))
    # )

    # Ignore the part of the main menu message which has the randovania version in it
    data["gameConfig"]["mainMenuMessage"] = data["gameConfig"]["mainMenuMessage"].split("\n")[1]
    expected_data["gameConfig"]["mainMenuMessage"] = expected_data["gameConfig"]["mainMenuMessage"].split("\n")[1]

    data["gameConfig"]["resultsString"] = data["gameConfig"]["resultsString"].split("|")[1]
    expected_data["gameConfig"]["resultsString"] = expected_data["gameConfig"]["resultsString"].split("|")[1]

    assert data == expected_data


@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename"),
    [
        ("prime1_and_2_multi.rdvgame", "randomprime_expected_data.json"),  # simple multi
        ("prime1_crazy_seed.rdvgame", "randomprime_expected_data_crazy.json"),  # chaos features
        ("prime1_crazy_seed_one_way_door.rdvgame", "randomprime_expected_data_one_way_door.json"),
        # same as above but 1-way doors
    ]
)
def test_create_patch_data(test_files_dir, rdvgame_filename, expected_results_filename, mocker):
    rdvgame = test_files_dir.joinpath("log_files", rdvgame_filename)
    expected_results = test_files_dir.joinpath(expected_results_filename)
    _test_preset(rdvgame, expected_results, mocker)
