import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.ammo_state import AmmoState


@pytest.fixture(
    params=[
        {"encoded": b'\x16', "json": {"variance": 0, "pickup_count": 5, }},
        {"encoded": b'\xf2', "json": {"variance": 0, "pickup_count": 60, }},
    ],
    name="state_with_data")
def _state_with_data(request):
    return request.param["encoded"], AmmoState.from_json(request.param["json"])


def test_decode(state_with_data):
    # Setup
    data, expected = state_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoState.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(state_with_data):
    # Setup
    expected, value = state_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
