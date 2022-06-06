import copy

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.games.game import RandovaniaGame
from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration

core_blank_json = {
    "mode": "two-way",
    "types_state": {
        "door": {
            "can_change_from": [
                "Back-Only Door",
                "Blue Key Door",
                "Explosive Door",
                "Locked Door",
                "Normal Door"
            ],
            "can_change_to": [
                "Back-Only Door",
                "Blue Key Door",
                "Explosive Door",
                "Locked Door",
                "Normal Door"
            ]
        },
        "other": {
            "can_change_from": [],
            "can_change_to": []
        }
    }
}


@pytest.fixture(
    params=[
        {"encoded": b'\x00\x00', "bit_count": 15, "json": {}},
    ],
    name="trick_level_data")
def _trick_level_data(request, mocker, blank_game_description):
    return (request.param["encoded"], request.param["bit_count"],
            DockRandoConfiguration.from_json(request.param["json"], game=RandovaniaGame.BLANK))


@pytest.fixture(
    params=[
        {"game": RandovaniaGame.BLANK, "encoded": b'@', "json_override": {}},
    ],
    name="config_with_data")
def _config_with_data(request):
    game: RandovaniaGame = request.param["game"]

    default = DockRandoConfiguration.from_json(core_blank_json, game)
    data = copy.deepcopy(core_blank_json)
    data.update(request.param["json_override"])

    config = DockRandoConfiguration.from_json(data, game)
    return request.param["encoded"], config, default


def test_decode(config_with_data):
    # Setup
    data, expected, reference = config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = DockRandoConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(config_with_data):
    # Setup
    expected, value, reference = config_with_data

    # Run
    result = bitpacking.pack_value(value, metadata={"reference": reference})

    # Assert
    assert result == expected
