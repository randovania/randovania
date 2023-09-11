from __future__ import annotations

import copy

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration


@pytest.fixture(
    params=[
        {"game": RandovaniaGame.METROID_PRIME_ECHOES, "encoded": b"\x00", "pickups_state": {}},
        {
            "game": RandovaniaGame.METROID_PRIME_ECHOES,
            "encoded": b"\x8aH\x80",
            "pickups_state": {"Missile Expansion": {"ammo_count": [10], "pickup_count": 12}},
        },
        {
            "game": RandovaniaGame.METROID_PRIME_ECHOES,
            "encoded": b"\x8fH\x80",
            "pickups_state": {"Missile Expansion": {"ammo_count": [15], "pickup_count": 12}},
        },
        {"game": RandovaniaGame.METROID_PRIME_CORRUPTION, "encoded": b"\x00", "pickups_state": {}},
    ],
)
def config_with_data(request, test_files_dir):
    game: RandovaniaGame = request.param["game"]

    default_data = test_files_dir.read_json("pickup_database", f"{game.value}_default_state", "ammo-pickups.json")

    default = AmmoPickupConfiguration.from_json(default_data, game)
    data = copy.deepcopy(default_data)

    for key, value in request.param.get("pickups_state", {}).items():
        data["pickups_state"][key] = value

    for key, value in request.param.get("maximum_ammo", {}).items():
        data["maximum_ammo"][key] = value

    config = AmmoPickupConfiguration.from_json(data, game)
    return request.param["encoded"], config, default


def test_decode(config_with_data):
    # Setup
    data, expected, reference = config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoPickupConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(config_with_data):
    # Setup
    expected, value, reference = config_with_data

    # Run
    result = bitpacking.pack_value(value, metadata={"reference": reference})

    # Assert
    assert result == expected
