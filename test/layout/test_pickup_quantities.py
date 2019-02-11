import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.pickup_quantities import PickupQuantities


@pytest.fixture(
    params=[
        {"encoded": b'\x00',
         "json": {}},

        {"encoded": b'\x87S,X\x88\xe6\xc4\x04\x10',
         "json": {"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 0}},

        {"encoded": b'\x85[,"9\xb1\x01\x04',
         "json": {"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 1}},

        {"encoded": b'\x85S\x16\xa29qM\x88\x08 ',
         "json": {"Missile Expansion": 10, "Light Suit": 0, "Super Missile": 0}},

        {"encoded": b'\x81Z#\x98\x14\xe0\x80\x82,\x08',
         "json": {"Missile Expansion": 10, "Light Suit": 2, "Super Missile": 1}},

        {"encoded": b'\x81b#\x98\x14\xe0\x80\x82\x00',
         "json": {"Missile Expansion": 10, "Super Missile": 1}},
    ],
    name="resources_with_data")
def _resources_with_data(request):
    return request.param["encoded"], PickupQuantities.from_params(request.param["json"])


def test_decode(resources_with_data):
    # Setup
    data, expected = resources_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = PickupQuantities.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(resources_with_data):
    # Setup
    expected, value = resources_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
