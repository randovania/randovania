import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.shuffled_items import ShuffledItems


@pytest.fixture(
    params=[
        {"encoded": b'\xf8',
         "json": ShuffledItems.default().as_json},

        {"encoded": b'\xff',
         "json": {
             key: True
             for key in ShuffledItems.default().as_json.keys()
         }},

        {"encoded": b'\x00',
         "json": {
             key: False
             for key in ShuffledItems.default().as_json.keys()
         }},

        {"encoded": b'$',
         "json": {
             "sky_temple_keys": False,
             "dark_temple_keys": False,
             "missile_launcher": True,
             "morph_ball_bombs": False,
             "space_jump": False,
             "scan_visor": True,
             "morph_ball": False,
             "charge_beam": False,
         }},
    ],
    name="shuffled_items_with_data")
def _layout_config_with_data(request):
    yield request.param["encoded"], ShuffledItems.from_json(request.param["json"])


def test_decode(shuffled_items_with_data):
    # Setup
    data, expected = shuffled_items_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = ShuffledItems.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(shuffled_items_with_data):
    # Setup
    expected, value = shuffled_items_with_data

    # Run
    result = bitpacking.pack_value(value)
    print(result)

    # Assert
    assert result == expected
