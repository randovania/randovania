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
        "worlds": [],
    }

    s = io.StringIO()
    s_io: TextIO = s
    json.dump({
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


def test_hello_world():
    input_data = {
        "format_version": binary_data.current_format_version,
        "game": 2,
        "game_name": "Metroid Prime 2: Echoes",
        "resource_database": {
            "items": [
                {
                    "index": 0,
                    "long_name": "Power Beam",
                    "short_name": "Power"
                },
                {
                    "index": 1,
                    "long_name": "Dark Beam",
                    "short_name": "Dark"
                },
            ],
            "events": [
                {
                    "index": 1,
                    "long_name": "Industrial Site Gate",
                    "short_name": "Event1"
                }
            ],
            "tricks": [
                {
                    "index": 0,
                    "long_name": "Combat/Scan Dash",
                    "short_name": "Dash"
                }
            ],
            "damage": [
                {
                    "index": 0,
                    "long_name": "Heal",
                    "short_name": "Heal",
                    "reductions": []
                },
                {
                    "index": 2,
                    "long_name": "Dark World (reduced with Dark Suit)",
                    "short_name": "DarkWorld1",
                    "reductions": [
                        {
                            "index": 13,
                            "multiplier": 0.20000000298023224
                        },
                        {
                            "index": 14,
                            "multiplier": 0.0
                        }
                    ]
                },
                {
                    "index": 3,
                    "long_name": "Dark World (immune with Dark Suit)",
                    "short_name": "DarkWorld2",
                    "reductions": [
                        {
                            "index": 13,
                            "multiplier": 0.0
                        },
                        {
                            "index": 14,
                            "multiplier": 0.0
                        }
                    ]
                }
            ],
            "versions": [
                {
                    "index": 0,
                    "long_name": "NTSC",
                    "short_name": "NTSC"
                }
            ],
            "misc": [
                {
                    "index": 0,
                    "long_name": "No Requirements",
                    "short_name": "None"
                },
                {
                    "index": 1,
                    "long_name": "Impossible To Reach",
                    "short_name": "Impossible"
                },
                {
                    "index": 2,
                    "long_name": "Will Stay Out Of Bounds",
                    "short_name": "StayOoB"
                }
            ],
            "difficulty": [
                {
                    "index": 0,
                    "long_name": "Difficulty Level",
                    "short_name": "Difficulty"
                }
            ],
        },
        "dock_weakness_database": {
            "door": [
                {
                    "index": 0,
                    "name": "Normal Door",
                    "is_blast_door": False,
                    "requirement_set": [
                        []
                    ]
                },
                {
                    "index": 1,
                    "name": "Dark Door",
                    "is_blast_door": False,
                    "requirement_set": [
                        [
                            {
                                "requirement_type": 0,
                                "requirement_index": 1,
                                "amount": 1,
                                "negate": False
                            }
                        ]
                    ]
                },
                {
                    "index": 8,
                    "name": "Permanently Locked",
                    "is_blast_door": False,
                    "requirement_set": []
                }
            ],
            "portal": [
                {
                    "index": 0,
                    "name": "Scan Portal",
                    "is_blast_door": False,
                    "requirement_set": [
                        []
                    ]
                }
            ]
        },
        "worlds": [
            {
                "name": "Test World",
                "asset_id": 1234,
                "areas": [
                    {
                        "name": "Test Area",
                        "asset_id": 97890,
                        "default_node_index": 1,
                        "nodes": [
                            {
                                "name": "Save Station",
                                "heal": True,
                                "node_type": 0,
                                "connections": {
                                    "Door": [[]]
                                }
                            },
                            {
                                "name": "Door",
                                "heal": True,
                                "node_type": 0,
                                "connections": {
                                    "Save Station": [
                                        [
                                            {
                                                "requirement_type": 0,
                                                "requirement_index": 1,
                                                "amount": 1,
                                                "negate": False
                                            }
                                        ]
                                    ]
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }

    x = binary_data.reference.build(input_data)

    b = io.BytesIO()
    binary_data.encode(input_data, b)

    # assert x == b.getvalue()


def test_world_stuff():
    input_data = {
        "name": "Test Area",
        "asset_id": 97890,
        "default_node_index": 1,
        "nodes": [
            {
                "name": "Save Station",
                "heal": True,
                "node_type": 0,
                "data": {},
            },
            {
                "name": "Door",
                "heal": True,
                "node_type": 1,
                "data": {
                    "dock_index": 0,
                    "connected_area_asset_id": 2679590972,
                    "connected_dock_index": 0,
                    "dock_type": 0,
                    "dock_weakness_index": 0,
                }
            }
        ],
        "connections": [
            [
                [[]],
            ],
            [
                [[
                    {
                        "requirement_type": 0,
                        "requirement_index": 1,
                        "amount": 1,
                        "negate": False
                    }
                ]]
            ]
        ]
    }

    x = binary_data.ConstructArea.build(input_data)
    decoded = binary_data.ConstructArea.parse(x)

    print(decoded)

    # assert x == b.getvalue()
