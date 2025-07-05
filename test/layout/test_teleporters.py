from __future__ import annotations

from typing import NamedTuple

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder
from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
)
from randovania.layout.lib.teleporters import (
    TeleporterConfiguration,
    TeleporterList,
    TeleporterShuffleMode,
    TeleporterTargetList,
)


class Data(NamedTuple):
    reference: TeleporterConfiguration | PrimeTrilogyTeleporterConfiguration
    encoded: bytes
    bit_count: int
    expected: TeleporterConfiguration | PrimeTrilogyTeleporterConfiguration
    description: str


def _m(
    encoded: bytes,
    bit_count: int,
    description: str,
    mode: str = "vanilla",
    skip_final_bosses=False,
    allow_unvisited_room_names=True,
    excluded_teleporters=None,
    excluded_targets=None,
):
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


def _g(
    encoded: bytes,
    bit_count: int,
    description: str,
    mode: str = "vanilla",
    excluded_teleporters=None,
    excluded_targets=None,
):
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
            "excluded_teleporters": excluded_teleporters,
            "excluded_targets": excluded_targets,
        },
    }


@pytest.fixture(
    params=[
        _g(b"\x00", 3, "Original connections"),
        _g(b"\xc0", 6, "One-way, with cycles", mode="one-way-teleporter"),
        _g(
            b"\xd8\x12",
            16,
            "One-way, with replacement; excluded 1 elevators",
            mode="one-way-teleporter-replacement",
            excluded_teleporters=[
                _a("Area 1", "Transport to Surface and Area 2", "Elevator to Surface East"),
                _a("Area 4 Crystal Mines", "Transport to Area 4", "Elevator to Central Caves"),
            ],
        ),
    ],
)
def test_generic_data(request):
    game = RandovaniaGame.METROID_SAMUS_RETURNS
    reference = TeleporterConfiguration(
        mode=TeleporterShuffleMode.VANILLA,
        excluded_teleporters=TeleporterList((), game),
        excluded_targets=TeleporterTargetList((), game),
    )
    return Data(
        reference=reference,
        encoded=request.param["encoded"],
        bit_count=request.param["bit_count"],
        expected=TeleporterConfiguration.from_json(request.param["json"], game=game),
        description=request.param["description"],
    )


@pytest.fixture(
    params=[
        _m(b"\x08", 5, "Original connections"),
        _m(b"\x18", 5, "Original connections", skip_final_bosses=True),
        _m(b"\xc1", 8, "One-way, with cycles", mode="one-way-teleporter"),
        _m(
            b"\xc81d",
            22,
            "One-way, with cycles; excluded 1 elevators",
            mode="one-way-teleporter",
            excluded_teleporters=[_a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple")],
        ),
        _m(
            b"\xe4\x033\x90",
            28,
            "One-way, anywhere; excluded 1 targets",
            mode="one-way-anything",
            excluded_targets=[_a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple")],
        ),
    ],
)
def test_echoes_data(request):
    game = RandovaniaGame.METROID_PRIME_ECHOES
    reference = PrimeTrilogyTeleporterConfiguration(
        mode=TeleporterShuffleMode.VANILLA,
        skip_final_bosses=False,
        allow_unvisited_room_names=False,
        excluded_teleporters=TeleporterList((), game),
        excluded_targets=TeleporterTargetList((), game),
    )
    return Data(
        reference=reference,
        encoded=request.param["encoded"],
        bit_count=request.param["bit_count"],
        expected=PrimeTrilogyTeleporterConfiguration.from_json(request.param["json"], game=game),
        description=request.param["description"],
    )


def test_decode(test_echoes_data, test_generic_data):
    # Run
    echoes_decoder = BitPackDecoder(test_echoes_data.encoded)
    echoes_result = PrimeTrilogyTeleporterConfiguration.bit_pack_unpack(
        echoes_decoder, {"reference": test_echoes_data.reference}
    )

    generic_decoder = BitPackDecoder(test_generic_data.encoded)
    generic_result = TeleporterConfiguration.bit_pack_unpack(
        generic_decoder, {"reference": test_generic_data.reference}
    )

    # Assert
    assert echoes_result == test_echoes_data.expected
    assert generic_result == test_generic_data.expected


def test_encode(test_echoes_data, test_generic_data):
    # Setup
    echoes_value = test_echoes_data.expected
    generic_value = test_generic_data.expected

    # Run
    echoes_result, echoes_bit_count = bitpacking.pack_results_and_bit_count(
        echoes_value.bit_pack_encode({"reference": test_echoes_data.reference})
    )
    generic_result, generic_bit_count = bitpacking.pack_results_and_bit_count(
        generic_value.bit_pack_encode({"reference": test_generic_data.reference})
    )

    # Assert
    assert echoes_result == test_echoes_data.encoded
    assert echoes_bit_count == test_echoes_data.bit_count

    assert generic_result == test_generic_data.encoded
    assert generic_bit_count == test_generic_data.bit_count


def test_description(test_echoes_data, test_generic_data):
    assert test_echoes_data.expected.description("elevators") == test_echoes_data.description
    assert test_generic_data.expected.description("elevators") == test_generic_data.description
