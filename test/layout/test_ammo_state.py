import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.item.ammo import Ammo
from randovania.layout.base.ammo_state import AmmoState


@pytest.fixture(
    params=[
        {"encoded": b'\x00 ', "json": {"ammo_count": [0], "pickup_count": 0, }},
        {"encoded": b'\x15\x06', "json": {"ammo_count": [10], "pickup_count": 5, }},
        {"encoded": b'e1`', "json": {"ammo_count": [50], "pickup_count": 60, "requires_major_item": False}},
        {"encoded": b'32\x9c', "json": {"ammo_count": [25], "pickup_count": 99, }},
    ],
    name="state_with_data")
def _state_with_data(request, echoes_item_database):
    ammo = echoes_item_database.ammo["Missile Expansion"]
    return request.param["encoded"], AmmoState.from_json(request.param["json"]), ammo


def test_decode(state_with_data):
    # Setup
    data, expected, ammo = state_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoState.bit_pack_unpack(decoder, {"ammo": ammo})

    # Assert
    assert result == expected


def test_encode(state_with_data):
    # Setup
    expected, value, ammo = state_with_data

    # Run
    result = bitpacking.pack_value(value, {"ammo": ammo})

    # Assert
    assert result == expected
