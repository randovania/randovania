import io
import json
from pathlib import Path

import pytest

from randovania import get_data_path
from randovania.game_description import data_reader
from randovania.games import binary_data


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
            "damage_reductions": [],
        },
        "starting_location": {
            "world_asset_id": 1006255871,
            "area_asset_id": 1655756413
        },
        "initial_states": {
            "Default": [
            ]
        },
        "minimal_logic": None,
        "victory_condition": {
            "type": "and",
            "data": {"comment": None, "items": []},
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


def _comparable_dict(value):
    if isinstance(value, dict):
        return [
            (key, _comparable_dict(item))
            for key, item in value.items()
        ]

    if isinstance(value, list):
        return [_comparable_dict(item) for item in value]

    return value


def test_full_data_encode_is_equal(game_enum):
    # The json data may be missing if we're running using a Pyinstaller binary
    # Setup
    data_dir = get_data_path().joinpath("json_data", game_enum.value)
    if not data_dir.is_dir() and get_data_path().joinpath("binary_data", f"{game_enum.value}.bin").is_file():
        pytest.skip("Missing json-based data")

    json_database = data_reader.read_split_file(data_dir)

    b = io.BytesIO()
    binary_data.encode(json_database, b)

    b.seek(0)
    decoded_database = binary_data.decode(b)

    # Run
    assert json_database == decoded_database

    comparable_json = _comparable_dict(json_database)
    comparable_binary = _comparable_dict(decoded_database)
    for a, b in zip(comparable_json, comparable_binary):
        assert a == b

    assert comparable_json == comparable_binary


@pytest.mark.parametrize("req", [
    {"type": "or", "data": {"comment": None, "items": []}},
    {"type": "and", "data": {"comment": None, "items": []}},
    {"type": "resource", "data": {"type": 2, "index": 5, "amount": 7, "negate": True}},
    {"type": "template", "data": "Example Template"},
])
def test_encode_requirement_simple(req):
    # Run
    encoded = binary_data.ConstructRequirement.build(req)
    decoded = binary_data.convert_to_raw_python(binary_data.ConstructRequirement.parse(encoded))

    # Assert
    assert req == decoded


def test_encode_requirement_complex():
    # Setup
    req = {
        "type": "and",
        "data": {
            "comment": None,
            "items": [
                {"type": "or", "data": {"comment": None, "items": []}},
                {"type": "and", "data": {"comment": None, "items": []}},
                {"type": "or", "data": {"comment": None, "items": []}},
                {"type": "resource", "data": {"type": 2, "index": 5, "amount": 7, "negate": True}},
                {"type": "or", "data": {"comment": None, "items": []}},
                {"type": "template", "data": "Example Template"},
            ]
        }
    }

    # Run
    encoded = binary_data.ConstructRequirement.build(req)
    decoded = binary_data.convert_to_raw_python(binary_data.ConstructRequirement.parse(encoded))

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
                "data": {"comment": None, "items": []}
            }
        },
        "damage_reductions": [],
    }
    resource_database["requirement_template"] = list(resource_database["requirement_template"].items())

    # Run
    encoded = binary_data.ConstructResourceDatabase.build(resource_database)

    # Assert
    assert encoded == b'\x00\x00\x00\x00\x00\x00\x01Foo\x00\x02\x00\x00\x00\x00\x01\x00\x01\x00'
