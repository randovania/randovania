import io
import json
from typing import BinaryIO, TextIO

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
        "starting_world_asset_id": 1006255871,
        "starting_area_asset_id": 1655756413,
        "starting_items": {},
        "item_loss_items": {},
        "victory_condition": [],
        "dock_weakness_database": {
            "door": [],
            "portal": []
        },
        "pickups": {},
        "original_pickup_indices_values": [],
        "worlds": [],
    }

    s = io.StringIO()
    s_io: TextIO = s
    json.dump({
        "pickups": sample_data["pickups"],
        "original_pickup_indices_values": sample_data["original_pickup_indices_values"],
        "starting_world_asset_id": sample_data["starting_world_asset_id"],
        "starting_area_asset_id": sample_data["starting_area_asset_id"],
        "victory_condition": sample_data["victory_condition"],
        "starting_items": sample_data["starting_items"],
        "item_loss_items": sample_data["item_loss_items"],
    }, s)

    b = io.BytesIO()
    b_io: BinaryIO = b
    binary_data.encode(sample_data, b_io)

    s.seek(0)
    b.seek(0)
    decoded = binary_data.decode(b_io, s_io)

    assert sample_data == decoded


def test_complex_encode(test_files_dir):
    with test_files_dir.join("prime_data_as_json.json").open("r") as data_file:
        data = json.load(data_file)
    b = io.BytesIO()
    b_io = b  # type: BinaryIO

    # Run
    binary_data.encode(data, b_io)

    # Assert
    assert test_files_dir.join(
        "prime_data_as_binary.bin").read_binary() == b.getvalue()


def test_complex_decode(test_files_dir):
    # Run
    decoded_data = binary_data.decode_file_path(
        str(test_files_dir.join("prime_data_as_binary.bin")),
        str(test_files_dir.join("prime_extra_data.json"))
    )

    # Assert
    with test_files_dir.join("prime_data_as_json.json").open("r") as data_file:
        saved_data = json.load(data_file)

    assert decoded_data == saved_data
