import dataclasses
from unittest.mock import PropertyMock, MagicMock
from pathlib import Path

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.samus_returns.exporter.patch_data_factory import MSRPatchDataFactory, MSRAcquiredMemo, \
    get_resources_for_details
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches, MSRMissileCosmeticType
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.base.ammo_pickup_state import AmmoPickupState
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
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
    rdvgame = test_files_dir.joinpath("log_files", "msr", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = MSRCosmeticPatches()
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
                 new_callable=PropertyMock, return_value="Words Hash")
    mocker.patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
                 new_callable=PropertyMock, return_value="$$$$$")

    # Run
    data = MSRPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "msr", expected_results_filename)
    expected_data = json_lib.read_path(expected_results_path)

    assert data == expected_data