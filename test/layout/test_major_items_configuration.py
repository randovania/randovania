import json

import pytest

from randovania import get_data_path
from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.default_database import default_prime2_item_database
from randovania.layout.major_items_configuration import MajorItemsConfiguration


@pytest.fixture(
    params=[
        {"encoded": b'\x00', "replace": {}},
        {"encoded": b'\x05\n', "replace": {
            "Spider Ball": {
                "include_copy_in_original_location": True,
                "num_shuffled_pickups": 1,
                "num_included_in_starting_items": 0,
                "included_ammo": []
            }
        }},
    ],
    name="location_with_data")
def _location_with_data(request):
    with get_data_path().joinpath("json_data", "configurations", "major_items", "default.json").open() as open_file:
        data = json.load(open_file)

    for key, value in request.param["replace"].items():
        data["items_state"][key] = value

    return request.param["encoded"], MajorItemsConfiguration.from_json(data, default_prime2_item_database())


def test_decode(location_with_data):
    # Setup
    data, expected = location_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = MajorItemsConfiguration.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(location_with_data):
    # Setup
    expected, value = location_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
