import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode, TeleporterList, \
    TeleporterTargetList


def _m(encoded: bytes, mode: str = "vanilla", skip_final_bosses=False,
       allow_unvisited_room_names=True, excluded_teleporters=None, excluded_targets=None):
    if excluded_teleporters is None:
        excluded_teleporters = []
    if excluded_targets is None:
        excluded_targets = []
    return {
        "encoded": encoded,
        "json": {
            "mode": mode,
            "skip_final_bosses": skip_final_bosses,
            "allow_unvisited_room_names": allow_unvisited_room_names,
            "excluded_teleporters": excluded_teleporters,
            "excluded_targets": excluded_targets,
        },
    }


def _a(world, area, instance_id=None):
    if instance_id is not None:
        return Teleporter(world, area, instance_id).as_json
    return AreaLocation(world, area).as_json


@pytest.fixture(
    params=[
        _m(b'\x08'),
        _m(b'\x18', skip_final_bosses=True),
        _m(b'\xb1', mode="one-way-elevator"),
        _m(b'\xb81d', mode="one-way-elevator", excluded_teleporters=[_a(1119434212, 1473133138, 122)]),
    ],
    name="with_data")
def _with_data(request):
    game = RandovaniaGame.METROID_PRIME_ECHOES
    reference = TeleporterConfiguration(
        mode=TeleporterShuffleMode.VANILLA,
        skip_final_bosses=False,
        allow_unvisited_room_names=False,
        excluded_teleporters=TeleporterList(frozenset(), game),
        excluded_targets=TeleporterTargetList(frozenset(), game),
    )
    return reference, request.param["encoded"], TeleporterConfiguration.from_json(request.param["json"], game=game)


def test_decode(with_data):
    # Setup
    reference, data, expected = with_data

    # Run
    decoder = BitPackDecoder(data)
    result = TeleporterConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(with_data):
    # Setup
    reference, expected, value = with_data

    # Run
    result = bitpacking._pack_encode_results([
        (value_argument, value_format)
        for value_argument, value_format in value.bit_pack_encode({"reference": reference})
    ])

    # Assert
    assert result == expected
