import io
import json
import os
from pathlib import Path
from typing import BinaryIO, TextIO

from randovania import get_data_path
from randovania.games.prime import binary_data


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
        "initial_states": {
            "Default": {
                "starting_world_asset_id": 1006255871,
                "starting_area_asset_id": 1655756413,
                "initial_resources": [
                ]
            }
        },
        "victory_condition": [],
        "dock_weakness_database": {
            "door": [],
            "portal": []
        },
        "pickup_database": {
            "pickups": {},
            "original_indices": [],
        },
        "worlds": [],
    }

    s = io.StringIO()
    s_io: TextIO = s
    json.dump({
        "pickup_database": sample_data["pickup_database"],
        "initial_states": sample_data["initial_states"],
        "victory_condition": sample_data["victory_condition"],
    }, s)

    b = io.BytesIO()
    b_io: BinaryIO = b
    binary_data.encode(sample_data, b_io)

    s.seek(0)
    b.seek(0)
    decoded = binary_data.decode(b_io, s_io)

    assert sample_data == decoded


def test_complex_encode(test_files_dir):
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        data = json.load(data_file)
    b = io.BytesIO()
    b_io = b  # type: BinaryIO

    # Run
    binary_data.encode(data, b_io)

    # Assert
    assert test_files_dir.joinpath(
        "prime_data_as_binary.bin").read_bytes() == b.getvalue()


def test_complex_decode(test_files_dir):
    # Run
    decoded_data = binary_data.decode_file_path(
        Path(test_files_dir.joinpath("prime_data_as_binary.bin")),
        Path(test_files_dir.joinpath("prime_extra_data.json"))
    )

    # Assert
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        saved_data = json.load(data_file)

    assert decoded_data == saved_data


def test_full_file_round_trip():
    with get_data_path().joinpath("binary_data", "prime2.bin").open("rb") as binary_file:
        input_io = io.BytesIO(binary_file.read())

    with get_data_path().joinpath("binary_data", "prime2_extra.json").open("r") as extra:
        decoded = binary_data.decode(input_io, extra)

    output_io = io.BytesIO()
    b_io = output_io  # type: BinaryIO

    # Run
    binary_data.encode(decoded, b_io)

    # Assert
    assert input_io.getvalue() == output_io.getvalue()
