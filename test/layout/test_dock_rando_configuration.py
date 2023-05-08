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
        {"game": RandovaniaGame.BLANK, "encoded": b'@'},
        {"game": RandovaniaGame.BLANK, "encoded": b'J\x05\x00', "can_change_to": ["Explosive Door"]},
    ],
    name="config_with_data")
def _config_with_data(request):
    game: RandovaniaGame = request.param["game"]

    default = DockRandoConfiguration.from_json(core_blank_json, game)
    data = copy.deepcopy(core_blank_json)

    if "can_change_from" in request.param:
        data["types_state"]["door"]["can_change_from"] = request.param["can_change_from"]

    if "can_change_to" in request.param:
        data["types_state"]["door"]["can_change_to"] = request.param["can_change_to"]

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


def test_prime_thing(default_prime_configuration):
    config = {
        "mode": "two-way",
        "types_state": {
            "door": {
                "can_change_from": [
                    "Ice Door",
                    "Missile Blast Shield",
                    "Normal Door",
                    "Plasma Door",
                    "Wave Door"
                ],
                "can_change_to": [
                    "Ice Door",
                    "Ice Spreader Blast Shield",
                    "Missile Blast Shield (randomprime)",
                    "Normal Door",
                    "Plasma Door",
                    "Power Bomb Blast Shield",
                    "Super Missile Blast Shield",
                    "Wave Door"
                ]
            },
            "morph_ball": {
                "can_change_from": [],
                "can_change_to": []
            },
            "other": {
                "can_change_from": [],
                "can_change_to": []
            }
        }
    }
    ref = {"reference": default_prime_configuration.dock_rando}

    dc = DockRandoConfiguration.from_json(config, RandovaniaGame.METROID_PRIME)
    encoded = bitpacking.pack_value(dc, metadata=ref)

    decoder = BitPackDecoder(encoded)
    decoded = DockRandoConfiguration.bit_pack_unpack(decoder, ref)

    assert dc == decoded
