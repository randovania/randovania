import json

import pytest

from randovania import get_data_path
from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.ammo_configuration import AmmoConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\xaa\n\xfa\xfaB P\xa0\x00', "replace": {}},
    ],
    name="config_with_data")
def _config_with_data(request):
    with get_data_path().joinpath("json_data", "configurations", "ammo", "split-ammo.json").open() as open_file:
        data = json.load(open_file)

    for key, value in request.param["replace"].items():
        data["items_state"][key] = value

    return request.param["encoded"], AmmoConfiguration.from_json(data, default_prime2_item_database())


def test_decode(config_with_data):
    # Setup
    data, expected = config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoConfiguration.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(config_with_data):
    # Setup
    expected, value = config_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
