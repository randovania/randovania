from __future__ import annotations

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.base.ammo_pickup_state import AmmoPickupState


@pytest.fixture(
    params=[
        {"encoded": b"\x00\x10", "json": {"ammo_count": [0], "pickup_count": 0}},
        {"encoded": b"\x14\x83", "json": {"ammo_count": [10], "pickup_count": 5}},
        {"encoded": b"d\x98\xb0", "json": {"ammo_count": [50], "pickup_count": 60, "requires_main_item": False}},
        {"encoded": b"2\x99N", "json": {"ammo_count": [25], "pickup_count": 99}},
        {"encoded": b"\x0b0", "json": {"ammo_count": [-5], "pickup_count": 1}},
    ],
)
def state_with_data(request, echoes_pickup_database):
    ammo = echoes_pickup_database.ammo_pickups["Missile Expansion"]
    return request.param["encoded"], AmmoPickupState.from_json(request.param["json"]), ammo


def test_decode(state_with_data):
    # Setup
    data, expected, ammo = state_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoPickupState.bit_pack_unpack(decoder, {"ammo": ammo})

    # Assert
    assert result == expected


def test_encode(state_with_data):
    # Setup
    expected, value, ammo = state_with_data

    # Run
    result = bitpacking.pack_value(value, {"ammo": ammo})

    # Assert
    assert result == expected
