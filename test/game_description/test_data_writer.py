import io
import json

import pytest

import randovania
from randovania.game_description import data_reader, data_writer
from randovania.games.prime import default_data


def test_round_trip_full():
    original_data = default_data.decode_default_prime2()

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert original_data == encoded_data


def test_round_trip_small(test_files_dir):
    # Setup
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        original_data = json.load(data_file)

    game = data_reader.decode_data(original_data)
    encoded_data = data_writer.write_game_description(game)

    assert original_data == encoded_data


@pytest.mark.skipif(randovania.is_frozen(), reason="frozen executable doesn't have JSON files")
def test_commited_human_readable_description(echoes_game_description):
    buffer = io.StringIO()
    data_writer.write_human_readable_world_list(echoes_game_description, buffer)

    assert default_data.prime2_human_readable_path().read_text("utf-8") == buffer.getvalue()
