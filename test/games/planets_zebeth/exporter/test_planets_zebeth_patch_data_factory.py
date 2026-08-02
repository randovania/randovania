from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.games.planets_zebeth.exporter.patch_data_factory import PlanetsZebethPatchDataFactory
from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import PlanetsZebethCosmeticPatches
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.worlds_configuration import WorldsConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


@pytest.mark.usefixtures("_mock_seed_hash")
@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "starter_preset", 1),  # starter preset
    ],
)
def test_create_pickups_dict(test_files_dir, rdvgame_filename, expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "planets_zebeth", rdvgame_filename)
    worlds_config = WorldsConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = PlanetsZebethCosmeticPatches()
    mocker.patch("random.Random.randint", new_callable=MagicMock, return_value=0)

    data = PlanetsZebethPatchDataFactory(description, worlds_config, cosmetic_patches)

    db = data.game

    useless_target = PickupTarget(
        pickup_creator.create_nothing_pickup(db.get_resource_database_view(), "sItemNothing"),
        data.worlds_config.world_index,
    )

    text_data = data._get_item_data()
    memo_data = {}
    for key, value in text_data.items():
        memo_data[key] = value
    memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=data.patches.configuration.energy_per_tank)

    pickup_list = pickup_exporter.export_all_indices(
        data.patches,
        useless_target,
        data.game,
        data.rng,
        data.configuration.pickup_model_style,
        data.configuration.pickup_model_data_source,
        exporter=pickup_exporter.create_pickup_exporter(memo_data, data.worlds_config, data.game.game),
        visual_nothing=pickup_creator.create_visual_nothing(data.game_enum(), "sItemNothing"),
    )

    # Run
    pickups_dict = data._create_pickups_dict(pickup_list, data.rng)

    # Expected Result
    expected_results_path = test_files_dir.joinpath(
        "patcher_data", "planets_zebeth", "planets_zebeth", expected_results_filename, "world_1.json"
    )

    expected_data = json_lib.read_path(expected_results_path)

    assert pickups_dict == expected_data["level_data"]["pickups"]
