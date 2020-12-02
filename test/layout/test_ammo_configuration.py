import copy
import json

import pytest

from randovania import get_data_path
from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.layout.ammo_configuration import AmmoConfiguration


@pytest.fixture(
    params=[
        {"game": RandovaniaGame.PRIME2, "encoded": b'\x00\x00', "items_state": {}},
        {"game": RandovaniaGame.PRIME2, "encoded": b'"\x80\x00', "maximum_ammo": {"45": 20}},
        {"game": RandovaniaGame.PRIME2, "encoded": b'\t\x90',
         "items_state": {"Missile Expansion": {"variance": 0, "pickup_count": 12}}},
        {"game": RandovaniaGame.PRIME2, "encoded": b'"\x89\x90', "maximum_ammo": {"45": 20},
         "items_state": {"Missile Expansion": {"variance": 0, "pickup_count": 12}}},
        {"game": RandovaniaGame.PRIME3, "encoded": b'\x00', "items_state": {}},
        {"game": RandovaniaGame.PRIME3, "encoded": b'\x99\x00', "maximum_ammo": {"4": 50}},
    ],
    name="config_with_data")
def _config_with_data(request):
    game: RandovaniaGame = request.param["game"]

    with get_data_path().joinpath("item_database", game.value, "default_state", "ammo.json").open() as open_file:
        default_data = json.load(open_file)

    default = AmmoConfiguration.from_json(default_data, default_database.item_database_for_game(game))
    data = copy.deepcopy(default_data)

    for key, value in request.param.get("items_state", {}).items():
        data["items_state"][key] = value

    for key, value in request.param.get("maximum_ammo", {}).items():
        data["maximum_ammo"][key] = value

    config = AmmoConfiguration.from_json(data, default_database.item_database_for_game(game))
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
