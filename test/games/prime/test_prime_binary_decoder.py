import io
import json
from pathlib import Path
from typing import BinaryIO, TextIO

import pytest

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
        "starting_location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 1655756413
        },
        "initial_states": {
            "Default": [
            ]
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
        "starting_location": sample_data["starting_location"],
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

    with test_files_dir.joinpath("prime_extra_data.json").open("r") as data_file:
        extra_data = json.load(data_file)

    b = io.BytesIO()
    b_io = b  # type: BinaryIO

    # Run
    remaining_data = binary_data.encode(data, b_io)

    # Assert
    assert test_files_dir.joinpath("prime_data_as_binary.bin").read_bytes() == b.getvalue()
    assert extra_data == remaining_data


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
    # Setup
    json_database_path = get_data_path().joinpath("json_data", "prime2.json")
    if not json_database_path.exists():
        pytest.skip("Missing database")

    with json_database_path.open("r") as json_file:
        original_data = json.load(json_file)

    # Run 1
    output_io = io.BytesIO()
    remaining_data = binary_data.encode(original_data, output_io)

    # Run 2
    output_io.seek(0)
    text_io = io.StringIO(json.dumps(remaining_data))
    final_data = binary_data.decode(output_io, text_io)

    # Assert
    assert final_data == original_data
