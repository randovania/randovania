import json

import pytest

from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.dread.patcher.open_dread_patcher import OpenDreadPatcher
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription


@pytest.mark.xfail
def test_create_patch_data(test_files_dir, mocker):
    # Setup
    file = test_files_dir.joinpath("log_files", "dread_1.rdvgame")
    description = LayoutDescription.from_file(file)
    patcher = OpenDreadPatcher()
    players_config = PlayersConfiguration(0, {0: "Dread"})
    cosmetic_patches = DreadCosmeticPatches()

    # Run
    data = patcher.create_patch_data(description, players_config, cosmetic_patches)

    # Expected Result
    with test_files_dir.joinpath("dread_expected_data.json").open("r") as file:
        expected_data = json.load(file)

    assert data == expected_data
