from randovania.game_description import data_reader, data_writer
from randovania.games.prime import default_data


def test_round_trip():
    original_data = default_data.decode_default_prime2()

    game = data_reader.decode_data(original_data, False)
    encoded_data = data_writer.write_game_description(game)

    assert original_data == encoded_data

