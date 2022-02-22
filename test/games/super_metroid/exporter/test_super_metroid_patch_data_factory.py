import json

from randovania.games.super_metroid.exporter.patch_data_factory import SuperMetroidPatchDataFactory
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription


def test_patch_data_creation(test_files_dir):
    # Load the RDV game
    game_file = test_files_dir.joinpath("sdm_test_game.rdvgame").open()
    game_json = json.load(game_file)
    game_file.close()
    layout = LayoutDescription.from_json_dict(game_json)

    # Create patch_data from layout
    player_configuration = PlayersConfiguration(0, {0: "Player"})
    cosmetic_patches = SuperMetroidCosmeticPatches()

    patch_data = SuperMetroidPatchDataFactory(layout, player_configuration, cosmetic_patches).create_data()

    # Load control patch_data and compare the two for differences
    json_file = test_files_dir.joinpath("sdm_expected_result.json").open()
    expected_json = json.load(json_file)
    json_file.close()
    assert expected_json == patch_data
