import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.pickup_quantities import PickupQuantities


@pytest.fixture(
    params=[
        {"encoded": b'\x00',
         "json": {}},

        {"encoded": b'\x93Smd \xad6\xdb\xa8\x8el@A\x00',
         "json": {"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 0}},

        {"encoded": b'\x91[m\x08+M\xb6\xea#\x9b\x10\x10@',
         "json": {"Missile Expansion": 0, "Light Suit": 0, "Super Missile": 1}},

        {"encoded": b'\x91SY\x88+n8\xf2#\x97\x14\xd8\x80\x82\x00',
         "json": {"Missile Expansion": 10, "Light Suit": 0, "Super Missile": 0}},

        {"encoded": b'\x8dX\x82\xb8\xeb\xaf\xa29\x81N\x08\x08"\xc0\x80',
         "json": {"Missile Expansion": 10, "Light Suit": 2, "Super Missile": 1}},

        {"encoded": b'\x8d`\x82\xb8\xeb\xaf\xa29\x81N\x08\x08 ',
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
    print(result)

    # Assert
    assert result == expected
