from typing import NamedTuple

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode, TeleporterList, \
    TeleporterTargetList


class Data(NamedTuple):
    reference: TeleporterConfiguration
    encoded: bytes
    bit_count: int
    expected: TeleporterConfiguration
    description: str


def _m(encoded: bytes, bit_count: int, description: str, mode: str = "vanilla", skip_final_bosses=False,
       allow_unvisited_room_names=True, excluded_teleporters=None, excluded_targets=None):
    if excluded_teleporters is None:
        excluded_teleporters = []
    if excluded_targets is None:
        excluded_targets = []
    return {
        "encoded": encoded,
        "bit_count": bit_count,
        "description": description,
        "json": {
            "mode": mode,
            "skip_final_bosses": skip_final_bosses,
            "allow_unvisited_room_names": allow_unvisited_room_names,
            "excluded_teleporters": excluded_teleporters,
            "excluded_targets": excluded_targets,
        },
    }


def _a(region, area, instance_id=None):
    if instance_id is not None:
        return NodeIdentifier.create(region, area, instance_id).as_json
    return AreaIdentifier(region, area).as_json


@pytest.fixture(
    params=[
        _m(b'\x08', 5, 'Original connections'),
        _m(b'\x18', 5, 'Original connections', skip_final_bosses=True),
        _m(b'\xc1', 8, 'One-way, elevator room with cycles', mode="one-way-elevator"),
        _m(b'\xc81d', 22, 'One-way, elevator room with cycles; excluded 1 teleporters',
           mode="one-way-elevator", excluded_teleporters=[
                _a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple - Temple Transport C")
            ]),
        _m(b'\xe4\x03,\xd0', 28, 'One-way, anywhere; excluded 1 targets', mode="one-way-anything", excluded_targets=[
            _a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple - Temple Transport C")
        ]),
    ],
    name="test_data")
def _test_data(request):
    game = RandovaniaGame.METROID_PRIME_ECHOES
    reference = TeleporterConfiguration(
        mode=TeleporterShuffleMode.VANILLA,
        skip_final_bosses=False,
        allow_unvisited_room_names=False,
        excluded_teleporters=TeleporterList(tuple(), game),
        excluded_targets=TeleporterTargetList(tuple(), game),
    )
    return Data(
        reference=reference,
        encoded=request.param["encoded"],
        bit_count=request.param["bit_count"],
        expected=TeleporterConfiguration.from_json(request.param["json"], game=game),
        description=request.param["description"],
    )


def test_decode(test_data):
    # Run
    decoder = BitPackDecoder(test_data.encoded)
    result = TeleporterConfiguration.bit_pack_unpack(decoder, {
        "reference": test_data.reference
    })

    # Assert
    assert result == test_data.expected


def test_encode(test_data):
    # Setup
    value = test_data.expected

    # Run
    result, bit_count = bitpacking.pack_results_and_bit_count(value.bit_pack_encode({
        "reference": test_data.reference
    }))

    # Assert
    assert result == test_data.encoded
    assert bit_count == test_data.bit_count


def test_description(test_data):
    assert test_data.expected.description() == test_data.description
