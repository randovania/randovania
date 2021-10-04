import copy
import json

import pytest

from randovania import get_data_path
from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_configuration import AmmoConfiguration


@pytest.fixture(
    params=[
        {"game": RandovaniaGame.METROID_PRIME_ECHOES, "encoded": b'\x00', "items_state": {}},
        {"game": RandovaniaGame.METROID_PRIME_ECHOES, "encoded": b'\x8a\x91\x00',
         "items_state": {"Missile Expansion": {"ammo_count": [10], "pickup_count": 12}}},
        {"game": RandovaniaGame.METROID_PRIME_ECHOES, "encoded": b'\x8f\x91\x00',
         "items_state": {"Missile Expansion": {"ammo_count": [15], "pickup_count": 12}}},
        {"game": RandovaniaGame.METROID_PRIME_CORRUPTION, "encoded": b'\x00', "items_state": {}},
    ],
    name="config_with_data")
def _config_with_data(request):
    game: RandovaniaGame = request.param["game"]

    with get_data_path().joinpath("item_database", game.value, "default_state", "ammo.json").open() as open_file:
        default_data = json.load(open_file)

    default = AmmoConfiguration.from_json(default_data, game)
    data = copy.deepcopy(default_data)

    for key, value in request.param.get("items_state", {}).items():
        data["items_state"][key] = value

    for key, value in request.param.get("maximum_ammo", {}).items():
        data["maximum_ammo"][key] = value

    config = AmmoConfiguration.from_json(data, game)
    return request.param["encoded"], config, default


def test_decode(config_with_data):
    # Setup
    data, expected, reference = config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = AmmoConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(config_with_data):
    # Setup
    expected, value, reference = config_with_data

    # Run
    result = bitpacking.pack_value(value, metadata={"reference": reference})

    # Assert
    assert result == expected
