import json

import pytest

from randovania.game_description import data_reader, data_writer
from randovania.games import default_data
from randovania.games.game import RandovaniaGame


@pytest.mark.parametrize("game_enum", RandovaniaGame)
def test_round_trip_full(game_enum: RandovaniaGame):
    original_data = default_data.read_json_then_binary(game_enum)[1]

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert list(encoded_data.keys()) == list(original_data.keys())
    assert encoded_data == original_data


@pytest.mark.parametrize("small_name", ["prime_data_as_json.json", "prime2_small.json"])
def test_round_trip_small(test_files_dir, small_name):
    # Setup
    with test_files_dir.joinpath(small_name).open("r") as data_file:
        original_data = json.load(data_file)

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    # # Uncomment the following to update the file
    # with test_files_dir.joinpath(small_name).open("w", encoding="utf-8") as meta:
    #     json.dump(encoded_data, meta, indent=4); assert False

    assert encoded_data == original_data
