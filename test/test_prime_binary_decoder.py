import io
import json
from typing import BinaryIO

from randovania import prime_binary_decoder


def test_simple_round_trip():
    sample_data = {
        "game": 2,
        "game_name": "Metroid Prime 2: Echoes",
        "resource_database": {
            "items": [],
            "events": [],
            "tricks": [],
            "damage": [],
            "versions": [],
            "misc": [],
            "difficulty": [],
        },
        "dock_weakness_database": {
            "door": [],
            "portal": []
        },
        "worlds": [],
    }

    b = io.BytesIO()
    b_io = b  # type: BinaryIO
    prime_binary_decoder.encode(sample_data, b_io)

    b.seek(0)
    decoded = prime_binary_decoder.decode(b_io)

    assert sample_data == decoded


def test_complex_encode(test_files_dir):
    with test_files_dir.join("prime_data_as_json.json").open("r") as data_file:
        data = json.load(data_file)
    b = io.BytesIO()
    b_io = b  # type: BinaryIO

    # Run
    prime_binary_decoder.encode(data, b_io)

    # Assert
    assert test_files_dir.join("prime_data_as_binary.bin").read_binary() == b.getvalue()


def test_complex_decode(test_files_dir):
    # Run
    decoded_data = prime_binary_decoder.decode_file_path(str(test_files_dir.join("prime_data_as_binary.bin")))

    # Assert
    with test_files_dir.join("prime_data_as_json.json").open("r") as data_file:
        saved_data = json.load(data_file)

    assert decoded_data == saved_data


