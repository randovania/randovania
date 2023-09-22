from __future__ import annotations

import copy

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration


def _create_config_for(test_files_dir, game: RandovaniaGame, replace: dict):
    default_data = test_files_dir.read_json("pickup_database", f"{game.value}_default_state", "standard-pickups.json")

    default_data["minimum_random_starting_pickups"] = 0
    default_data["maximum_random_starting_pickups"] = 0

    data = copy.deepcopy(default_data)
    for field, value in replace.items():
        for key, inner_value in value.items():
            data[field][key] = inner_value

    return (
        StandardPickupConfiguration.from_json(default_data, game),
        StandardPickupConfiguration.from_json(data, game),
    )


@pytest.fixture(
    params=[
        {"encoded": b"\x00\x00\x00", "replace": {}},
        {
            "encoded": b"\x03\x1b\xa8\x00",
            "replace": {
                "pickups_state": {
                    "Spider Ball": {
                        "include_copy_in_original_location": True,
                        "num_shuffled_pickups": 1,
                        "num_included_in_starting_pickups": 0,
                        "included_ammo": [],
                    }
                }
            },
        },
    ],
)
def prime2_data(request, test_files_dir):
    return (
        request.param["encoded"],
        *_create_config_for(test_files_dir, RandovaniaGame.METROID_PRIME_ECHOES, request.param["replace"]),
    )


@pytest.fixture(
    params=[
        {"encoded": b"\x00\x00", "replace": {}},
    ],
)
def prime3_data(request, test_files_dir):
    return (
        request.param["encoded"],
        *_create_config_for(test_files_dir, RandovaniaGame.METROID_PRIME_CORRUPTION, request.param["replace"]),
    )


def test_decode_prime2(prime2_data):
    # Setup
    data, default, expected = prime2_data

    # Run
    decoder = BitPackDecoder(data)
    result = StandardPickupConfiguration.bit_pack_unpack(decoder, {"reference": default})

    # Assert
    assert result == expected


def test_encode_prime2(prime2_data):
    # Setup
    expected, default, value = prime2_data

    # Run
    result = bitpacking.pack_value(value, {"reference": default})

    # Assert
    assert result == expected


def test_encode_prime3(prime3_data):
    # Setup
    expected, default, value = prime3_data

    # Run
    result = bitpacking.pack_value(value, {"reference": default})

    # Assert
    assert result == expected
