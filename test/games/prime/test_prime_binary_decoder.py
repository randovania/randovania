import io
import json
from pathlib import Path

import pytest

from randovania import get_data_path
from randovania.games.game import RandovaniaGame
from randovania.games.prime import binary_data


def test_simple_round_trip():
    sample_data = {
        "game": "prime2",
        "resource_database": {
            "items": [],
            "energy_tank_item_index": 0,
            "item_percentage_index": 0,
            "multiworld_magic_item_index": 0,
            "events": [],
            "tricks": [],
            "damage": [],
            "versions": [],
            "misc": [],
            "requirement_template": {},
        },
        "game_specific": {
            "energy_per_tank": 100.0,
            "safe_zone_heal_per_second": 1.0,
            "beam_configurations": [],
            "dangerous_energy_tank": True,
        },
        "starting_location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 1655756413
        },
        "initial_states": {
            "Default": [
            ]
        },
        "victory_condition": {
            "type": "and",
            "data": []
        },
        "dock_weakness_database": {
            "door": [],
            "portal": [],
            "morph_ball": [],
        },
        "worlds": [],
    }

    b = io.BytesIO()
    binary_data.encode(sample_data, b)

    b.seek(0)
    decoded = binary_data.decode(b)

    assert decoded == sample_data


def test_complex_encode(test_files_dir):
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        data = json.load(data_file)

    b = io.BytesIO()

    # Run
    binary_data.encode(data, b)
    # Whenever the file format changes, we can use the following line to force update our test file
    # test_files_dir.joinpath("prime_data_as_binary.bin").write_bytes(b.getvalue()); assert False

    # Assert
    assert test_files_dir.joinpath("prime_data_as_binary.bin").read_bytes() == b.getvalue()


def test_complex_decode(test_files_dir):
    # Run
    decoded_data = binary_data.decode_file_path(Path(test_files_dir.joinpath("prime_data_as_binary.bin")))

    # Assert
    with test_files_dir.joinpath("prime_data_as_json.json").open("r") as data_file:
        saved_data = json.load(data_file)

    assert decoded_data == saved_data


@pytest.mark.parametrize("game", RandovaniaGame)
def test_full_file_round_trip(game):
    # Setup
    json_database_path = get_data_path().joinpath("json_data", f"{game.value}.json")
    if not json_database_path.exists():
        pytest.skip("Missing database")

    with json_database_path.open("r") as json_file:
        original_data = json.load(json_file)

    # Run 1
    output_io = io.BytesIO()
    binary_data.encode(original_data, output_io)

    # Run 2
    output_io.seek(0)
    final_data = binary_data.decode(output_io)

    # Assert
    assert final_data == original_data


def _comparable_dict(value):
    if isinstance(value, dict):
        return [
            (key, _comparable_dict(item))
            for key, item in value.items()
        ]

    if isinstance(value, list):
        return [_comparable_dict(item) for item in value]

    return value


@pytest.mark.skipif(
    not get_data_path().joinpath("json_data", "prime2.json").is_file(),
    reason="Missing prime2.json"
)
def test_full_data_encode_is_equal():
    # The prime2.json may be missing if we're running using a Pyinstaller binary
    # Setup
    json_database_file = get_data_path().joinpath("json_data", "prime2.json")

    with json_database_file.open("r") as open_file:
        json_database = json.load(open_file)

    b = io.BytesIO()
    binary_data.encode(json_database, b)

    b.seek(0)
    decoded_database = binary_data.decode(b)

    # Run
    assert json_database == decoded_database

    comparable_json = _comparable_dict(json_database)
    comparable_binary = _comparable_dict(decoded_database)
    assert comparable_json == comparable_binary


@pytest.mark.parametrize("req", [
    {"type": "or", "data": []},
    {"type": "and", "data": []},
    {"type": "resource", "data": {"type": 2, "index": 5, "amount": 7, "negate": True}},
    {"type": "template", "data": "Example Template"},
])
def test_encode_requirement_simple(req):
    # Run
    encoded = binary_data.ConstructRequirement.build(req)
    decoded = binary_data._convert_to_raw_python(binary_data.ConstructRequirement.parse(encoded))

    # Assert
    assert req == decoded


def test_encode_requirement_complex():
    # Setup
    req = {
        "type": "and",
        "data": [
            {"type": "or", "data": []},
            {"type": "and", "data": []},
            {"type": "or", "data": []},
            {"type": "resource", "data": {"type": 2, "index": 5, "amount": 7, "negate": True}},
            {"type": "or", "data": []},
            {"type": "template", "data": "Example Template"},
        ]
    }

    # Run
    encoded = binary_data.ConstructRequirement.build(req)
    decoded = binary_data._convert_to_raw_python(binary_data.ConstructRequirement.parse(encoded))

    # Assert
    assert req == decoded


def test_encode_resource_database():
    # Setup
    resource_database = {
        "items": [],
        "energy_tank_item_index": 0,
        "item_percentage_index": 0,
        "multiworld_magic_item_index": 0,
        "events": [],
        "tricks": [],
        "damage": [],
        "versions": [],
        "misc": [],
        "requirement_template": {
            "Foo": {
                "type": "or",
                "data": []
            }
        },
    }
    resource_database["requirement_template"] = list(resource_database["requirement_template"].items())

    # Run
    encoded = binary_data.ConstructResourceDatabase.build(resource_database)

    # Assert
    assert encoded == b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01Foo\x00\x02\x00'
