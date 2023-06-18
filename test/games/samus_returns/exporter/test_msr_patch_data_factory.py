from unittest.mock import PropertyMock


from randovania.games.samus_returns.exporter.patch_data_factory import MSRPatchDataFactory
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


def test_create_patch_data(test_files_dir, mocker):
    # Setup
    file = test_files_dir.joinpath("log_files", "samus_returns", "starter_preset.rdvgame")
    description = LayoutDescription.from_file(file)
    players_config = PlayersConfiguration(0, {0: "Samus Returns"})
    cosmetic_patches = MSRCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    # Run
    data = MSRPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_data = json_lib.read_path(test_files_dir.joinpath("patcher_data", "samus_returns", "starter_preset.json"))

    assert data == expected_data