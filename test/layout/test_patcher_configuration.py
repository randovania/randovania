import copy

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.layout.patcher_configuration import PatcherConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\xc0', "json": {}},
        {"encoded": b'\x80', "json": {"warp_to_start": False}},
        {"encoded": b'@', "json": {"menu_mod": False}},
        {"encoded": b'\x00', "json": {"menu_mod": False, "warp_to_start": False}},
        {"encoded": b'H', "json": {"menu_mod": False, "pickup_model_data_source": "location"}},
        {"encoded": b'\xa0', "json": {"warp_to_start": False, "pickup_model_style": "hide-scan"}},
    ],
    name="patcher_with_data")
def _patcher_with_data(request):
    params = copy.copy(request.param["json"])
    for key, value in PatcherConfiguration.default().as_json.items():
        if key not in params:
            params[key] = value
    return request.param["encoded"], PatcherConfiguration.from_json_dict(params)


def test_decode(patcher_with_data):
    # Setup
    data, expected = patcher_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = PatcherConfiguration.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(patcher_with_data):
    # Setup
    expected, value = patcher_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
