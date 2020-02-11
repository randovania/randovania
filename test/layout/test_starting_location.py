import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.starting_location import StartingLocation


@pytest.fixture(
    params=[
        {"encoded": b'\x00\x00', "json": []},
        {"encoded": b'\x00a<', "json": ["Temple Grounds/Landing Site"]},
        {"encoded": b'\x00\xa3N(', "json": ["Agon Wastes/Save Station 1", "Agon Wastes/Save Station 2"]},
    ],
    name="location_with_data")
def _location_with_data(request):
    return request.param["encoded"], StartingLocation.from_json(request.param["json"])


def test_decode(location_with_data):
    # Setup
    data, expected = location_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = StartingLocation.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(location_with_data):
    # Setup
    expected, value = location_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
