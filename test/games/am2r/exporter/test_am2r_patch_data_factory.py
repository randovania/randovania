from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.exporter import pickup_exporter
from randovania.game_description.assignment import PickupTarget
from randovania.games.am2r.exporter.patch_data_factory import AM2RPatchDataFactory, _construct_music_shuffle_dict
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches, MusicMode
from randovania.generator.pickup_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


def test_construct_music_shuffle_dict_vanilla() -> None:
    music_dict = _construct_music_shuffle_dict(MusicMode.VANILLA, Random())

    assert music_dict == {}


def test_construct_music_shuffle_dict_type() -> None:
    excluded_list = [
        "musarea7d",
        "muscredits",
        "musending",
        "musintroseq",
    ]

    music_dict = _construct_music_shuffle_dict(MusicMode.TYPE, Random())

    for song in excluded_list:
        assert song not in music_dict
    assert len(music_dict) == 44


def test_construct_music_shuffle_dict_full() -> None:
    music_dict = _construct_music_shuffle_dict(MusicMode.FULL, Random())

    assert len(music_dict) == 48


@pytest.mark.usefixtures("_mock_seed_hash")
@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "shiny_pickups_dict_from_starter_preset.json", 1),  # starter preset
    ],
)
def test_create_pickups_dict_shiny(test_files_dir, rdvgame_filename, expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "am2r", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = AM2RCosmeticPatches()
    mocker.patch("random.Random.randint", new_callable=MagicMock, return_value=0)

    data = AM2RPatchDataFactory(description, players_config, cosmetic_patches)

    db = data.game

    useless_target = PickupTarget(
        pickup_creator.create_nothing_pickup(db.resource_database, "sItemNothing"), data.players_config.player_index
    )

    text_data = data._get_text_data()
    model_data = data._get_model_data()
    memo_data = {}
    for key, value in text_data.items():
        memo_data[key] = value["text_desc"]
    memo_data["Energy Tank"] = memo_data["Energy Tank"].format(Energy=data.patches.configuration.energy_per_tank)

    pickup_list = pickup_exporter.export_all_indices(
        data.patches,
        useless_target,
        data.game.region_list,
        data.rng,
        data.configuration.pickup_model_style,
        data.configuration.pickup_model_data_source,
        exporter=pickup_exporter.create_pickup_exporter(memo_data, data.players_config, data.game.game),
        visual_nothing=pickup_creator.create_visual_nothing(data.game_enum(), "sItemNothing"),
    )

    # Run
    pickups_dict = data._create_pickups_dict(pickup_list, text_data, model_data, data.rng)

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "am2r", expected_results_filename)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, pickups_dict); assert False

    expected_data = json_lib.read_path(expected_results_path)

    assert pickups_dict == expected_data
