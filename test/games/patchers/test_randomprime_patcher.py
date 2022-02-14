import json
import os
from unittest.mock import MagicMock, ANY, PropertyMock

import pytest

from randovania.game_description.resources.pickup_entry import PickupModel, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.patcher.randomprime_patcher import RandomprimePatcher, prime1_pickup_details_to_patcher
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.patching.prime.patcher_file_lib import pickup_exporter


@pytest.mark.parametrize("other_player", [False, True])
def test_prime1_pickup_details_to_patcher_shiny_missile(prime1_resource_database, other_player: bool):
    # Setup
    rng = MagicMock()
    rng.randint.return_value = 0
    detail = pickup_exporter.ExportedPickupDetails(
        index=PickupIndex(15),
        scan_text="Your Missile Expansion. Provides 5 Missiles",
        hud_text=["Missile Expansion acquired!"],
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
            'model': 'Missile',
            'scanText': 'Your Missile Expansion. Provides 5 Missiles',
            'hudmemoText': 'Missile Expansion acquired!',
        }
    else:
        shiny_stuff = {
            'model': 'Shiny Missile',
            'scanText': 'Your Shiny Missile Expansion. Provides 5 Missiles',
            'hudmemoText': 'Shiny Missile Expansion acquired!',
        }

    # Run
    result = prime1_pickup_details_to_patcher(detail, False, rng)

    # Assert
    assert result == {
        'type': 'Missile',
        'currIncrease': 6, 'maxIncrease': 6,
        'respawn': False,
        **shiny_stuff,
    }


def test_create_patch_data(test_files_dir, mocker):
    # Setup
    file = test_files_dir.joinpath("log_files", "prime1_and_2_multi.rdvgame")
    description = LayoutDescription.from_file(file)
    patcher = RandomprimePatcher()
    players_config = PlayersConfiguration(0, {0: "Prime", 1: "Echoes"})
    cosmetic_patches = PrimeCosmeticPatches(use_hud_color=True, hud_color=(255, 0, 0),
                                            suit_color_rotations=(0, 40, 350, 12))

    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash_bytes",
                 new_callable=PropertyMock,
                 return_value=b"\x00\x00\x00\x00\x00")

    # Run
    data = patcher.create_patch_data(description, players_config, cosmetic_patches)

    # Expected Result
    with test_files_dir.joinpath("randomprime_expected_data.json").open("r") as file:
        expected_data = json.load(file)

    # with test_files_dir.joinpath("randomprime_actual_data.json").open("w") as file:
    #     file.write(json.dumps(data))

    # Ignore the part of the main menu message which has the randovania version in it
    data["gameConfig"]["mainMenuMessage"] = data["gameConfig"]["mainMenuMessage"].split("\n")[1]
    expected_data["gameConfig"]["mainMenuMessage"] = expected_data["gameConfig"]["mainMenuMessage"].split("\n")[1]

    assert data == expected_data


def test_patch_game(mocker, tmp_path):
    mock_symbols_for_file: MagicMock = mocker.patch("py_randomprime.symbols_for_file", return_value={
        "UpdateHintState__13CStateManagerFf": 0x80044D38,
    })
    mock_patch_iso_raw: MagicMock = mocker.patch("py_randomprime.patch_iso_raw")
    patch_data = {"patch": "data", 'gameConfig': {}, 'hasSpoiler': True}
    game_files_path = MagicMock()
    progress_update = MagicMock()

    patcher = RandomprimePatcher()

    # Run
    patcher.patch_game(tmp_path.joinpath("input.iso"), tmp_path.joinpath("output.iso"),
                       patch_data, game_files_path, progress_update)

    # Assert
    expected = {
        "patch": "data",
        'gameConfig': {
            "updateHintStateReplacement": [
                148, 33, 255, 204, 124, 8, 2, 166, 144, 1, 0, 56, 191, 193, 0, 44, 124, 127, 27, 120, 136, 159, 0, 2,
                44, 4, 0, 0, 64, 130, 0, 24, 187, 193, 0, 44, 128, 1, 0, 56, 124, 8, 3, 166, 56, 33, 0, 52, 78,
                128, 0, 32, 56, 192, 0, 0, 152, 223, 0, 2, 63, 192, 128, 4, 99, 222, 77, 148, 56, 128, 1, 0, 124, 4,
                247, 172, 44, 4, 0, 0, 56, 132, 255, 224, 64, 130, 255, 244, 124, 0, 4, 172, 76, 0, 1, 44, 187,
                193, 0, 44, 128, 1, 0, 56, 124, 8, 3, 166, 56, 33, 0, 52, 78, 128, 0, 32
            ]
        },
        "inputIso": os.fspath(tmp_path.joinpath("input.iso")),
        "outputIso": os.fspath(tmp_path.joinpath("output.iso")),
    }
    mock_symbols_for_file.assert_called_once_with(tmp_path.joinpath("input.iso"))
    mock_patch_iso_raw.assert_called_once_with(json.dumps(expected, indent=4, separators=(',', ': ')), ANY)
