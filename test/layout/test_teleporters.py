import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode, TeleporterList, \
    TeleporterTargetList


def _m(encoded: bytes, bit_count: int, mode: str = "vanilla", skip_final_bosses=False,
       allow_unvisited_room_names=True, excluded_teleporters=None, excluded_targets=None):
    if excluded_teleporters is None:
        excluded_teleporters = []
    if excluded_targets is None:
        excluded_targets = []
    return {
        "encoded": encoded,
        "bit_count": bit_count,
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
        return NodeIdentifier.create(world, area, instance_id).as_json
    return AreaIdentifier(world, area).as_json


@pytest.fixture(
    params=[
        _m(b'\x08', 5),
        _m(b'\x18', 5, skip_final_bosses=True),
        _m(b'\xb1', 8, mode="one-way-elevator"),
        _m(b'\xb81d', 22, mode="one-way-elevator", excluded_teleporters=[
            _a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple - Temple Transport C")
        ]),
    ],
    name="with_data")
def _with_data(request):
    game = RandovaniaGame.METROID_PRIME_ECHOES
    reference = TeleporterConfiguration(
        mode=TeleporterShuffleMode.VANILLA,
        skip_final_bosses=False,
        allow_unvisited_room_names=False,
        excluded_teleporters=TeleporterList(tuple(), game),
        excluded_targets=TeleporterTargetList(tuple(), game),
    )
    return (reference, request.param["encoded"], request.param["bit_count"],
            TeleporterConfiguration.from_json(request.param["json"], game=game))


def test_decode(with_data):
    # Setup
    reference, data, _, expected = with_data

    # Run
    decoder = BitPackDecoder(data)
    result = TeleporterConfiguration.bit_pack_unpack(decoder, {"reference": reference})

    # Assert
    assert result == expected


def test_encode(with_data):
    # Setup
    reference, expected_bytes, expected_bit_count, value = with_data

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode({"reference": reference}))

    # Assert
    assert result == expected_bytes
    assert bit_count == expected_bit_count
