import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.patcher_configuration import PatcherConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\xf0', "json": {}},
        {"encoded": b'\xb0', "json": {"warp_to_start": False}},
        {"encoded": b'p', "json": {"menu_mod": False}},
        {"encoded": b'0', "json": {"menu_mod": False, "warp_to_start": False}},
        {"encoded": b'r', "json": {"menu_mod": False, "pickup_model_data_source": "location"}},
        {"encoded": b'\xb8', "json": {"warp_to_start": False, "pickup_model_style": "hide-scan"}},
        {"encoded": b'\xc1\xf4\x1f@\x00', "json": {"varia_suit_damage": 5.0, "dark_suit_damage": 20.0}},
    ],
    name="patcher_with_data")
def _patcher_with_data(request):
    return request.param["encoded"], PatcherConfiguration.from_json_dict(request.param["json"])


def test_decode(patcher_with_data):
    # Setup
    data, expected = patcher_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = PatcherConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(patcher_with_data):
    # Setup
    expected, value = patcher_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
