from unittest.mock import PropertyMock

import pytest

from randovania.games.am2r.exporter.patch_data_factory import AM2RPatchDataFactory
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "starter_preset.json", 1),                             # starter preset
    ]
)

def test_create_patch_data(test_files_dir, rdvgame_filename,
                            expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "am2r", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = AM2RCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    # Run
    data = AM2RPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "am2r", expected_results_filename)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, data)

    expected_data = json_lib.read_path(expected_results_path)

    assert data == expected_data
