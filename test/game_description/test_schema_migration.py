import json

import pytest

from randovania.game_description import data_reader, data_writer, game_migration


def test_round_trip_small(test_files_dir):
    # Setup
    with test_files_dir.joinpath("prime2_small_v1.json").open("r") as data_file:
        original_data = game_migration.migrate_to_current(json.load(data_file))

    game = data_reader.decode_data(original_data)

    encoded_data = data_writer.write_game_description(game)
    assert encoded_data == original_data


def test_round_trip_area_conflict(test_files_dir):
    with test_files_dir.joinpath("prime2_small_v1.json").open("r") as data_file:
        json_data = json.load(data_file)

    json_data["worlds"][0]["areas"].append(dict(json_data["worlds"][0]["areas"][0]))

    with pytest.raises(ValueError):
        game_migration.migrate_to_current(json_data)


def test_round_trip_node_conflict(test_files_dir):
    with test_files_dir.joinpath("prime2_small_v1.json").open("r") as data_file:
        json_data = json.load(data_file)

    json_data["worlds"][0]["areas"][0]["nodes"].append(dict(json_data["worlds"][0]["areas"][0]["nodes"][0]))

    with pytest.raises(ValueError):
        game_migration.migrate_to_current(json_data)
