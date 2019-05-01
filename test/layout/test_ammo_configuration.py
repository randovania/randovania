import json

import pytest

from randovania import get_data_path
from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.ammo_configuration import AmmoConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "items_state": {}},
        {"encoded": b'!@', "maximum_ammo": {"45": 20}},
        {"encoded": b'\x02\x0c\x80', "items_state": {"Missile Expansion": {"variance": 0, "pickup_count": 12}}},
        {"encoded": b'!B\x0c\x80', "maximum_ammo": {"45": 20},
         "items_state": {"Missile Expansion": {"variance": 0, "pickup_count": 12}}},
    ],
    name="config_with_data")
def _config_with_data(request):
    with get_data_path().joinpath("item_database", "default_state", "ammo.json").open() as open_file:
        data = json.load(open_file)

    for key, value in request.param.get("items_state", {}).items():
        data["items_state"][key] = value

    for key, value in request.param.get("maximum_ammo", {}).items():
        data["maximum_ammo"][key] = value

    return request.param["encoded"], AmmoConfiguration.from_json(data, default_prime2_item_database())


def test_decode(config_with_data):
    # Setup
    data, expected = config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(config_with_data):
    # Setup
    expected, value = config_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
