from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.games.fusion.exporter.patch_data_factory import FusionPatchDataFactory
from randovania.games.fusion.layout.fusion_cosmetic_patches import FusionCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


@pytest.mark.usefixtures("_mock_seed_hash")
@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "shiny_pickups_dict_from_starter_preset.json", 1),  # starter preset
    ],
)
def test_create_pickups_dict_shiny(test_files_dir, rdvgame_filename, expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "fusion", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = FusionCosmeticPatches()
    mocker.patch("random.Random.randint", new_callable=MagicMock, return_value=0)

    data = FusionPatchDataFactory(description, players_config, cosmetic_patches)

    db = data.game

    useless_target = PickupTarget(
        pickup_creator.create_nothing_pickup(db.get_resource_database_view(), "Empty"), data.players_config.player_index
    )

    memo_data = data.create_memo_data()

    pickup_list = pickup_exporter.export_all_indices(
        data.patches,
        useless_target,
        data.game.region_list,
        data.rng,
        data.configuration.pickup_model_style,
        data.configuration.pickup_model_data_source,
        exporter=pickup_exporter.create_pickup_exporter(memo_data, data.players_config, data.game.game),
        visual_nothing=pickup_creator.create_visual_nothing(data.game_enum(), "Empty"),
    )

    # Run
    pickups_dict = data._create_pickup_dict(pickup_list)

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "fusion", expected_results_filename)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, pickups_dict); assert False

    expected_data = json_lib.read_path(expected_results_path)

    assert pickups_dict == expected_data
