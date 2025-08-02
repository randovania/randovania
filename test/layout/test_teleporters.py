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
    num_valid_targets: int


def _m(
    encoded: bytes,
    bit_count: int,
    description: str,
    num_valid_targets: int = 22,
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
        "num_valid_targets": num_valid_targets,
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
    num_valid_targets: int,
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
        "num_valid_targets": num_valid_targets,
        "json": {
            "mode": mode,
            "excluded_teleporters": excluded_teleporters,
            "excluded_targets": excluded_targets,
        },
    }


@pytest.fixture(
    params=[
        _g(b"\x00", 3, "Original connections", 40),
        _g(b"\xc0", 6, "One-way, with cycles", 40, mode="one-way-teleporter"),
        _g(
            b"\xd8\x12",
            16,
            "One-way, with replacement; excluded 2 elevators",
            38,
            mode="one-way-teleporter-replacement",
            excluded_teleporters=[
                _a("Area 1", "Transport to Surface and Area 2", "Elevator to Surface East"),
                _a("Area 4 Crystal Mines", "Transport to Central Caves", "Elevator to Area 4 Central Caves"),
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
        num_valid_targets=request.param["num_valid_targets"],
    )


@pytest.fixture(
    params=[
        _m(b"\x08", 5, "Original connections", num_valid_targets=0),
        _m(b"\x18", 5, "Original connections", num_valid_targets=0, skip_final_bosses=True),
        _m(b"\xc1", 8, "One-way, with cycles", mode="one-way-teleporter"),
        _m(
            b"\xc81d",
            22,
            "One-way, with cycles; excluded 1 elevators",
            num_valid_targets=21,
            mode="one-way-teleporter",
            excluded_teleporters=[_a("Temple Grounds", "Temple Transport C", "Elevator to Great Temple")],
        ),
        _m(
            b"\xe4\x033\x90",
            28,
            "One-way, anywhere; excluded 1 targets",
            num_valid_targets=254,
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
        num_valid_targets=request.param["num_valid_targets"],
    )


def test_valid_targets_echoes(test_echoes_data):
    config = PrimeTrilogyTeleporterConfiguration(
        mode=test_echoes_data.expected.mode,
        skip_final_bosses=False,
        allow_unvisited_room_names=False,
        excluded_teleporters=test_echoes_data.expected.excluded_teleporters,
        excluded_targets=test_echoes_data.expected.excluded_targets,
    )

    valid_targets = config.valid_targets
    assert len(valid_targets) == test_echoes_data.num_valid_targets


def test_valid_targets_msr(test_generic_data):
    config = TeleporterConfiguration(
        mode=TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
        excluded_teleporters=test_generic_data.expected.excluded_teleporters,
        excluded_targets=test_generic_data.expected.excluded_targets,
    )

    valid_targets = config.valid_targets
    assert len(valid_targets) == test_generic_data.num_valid_targets


@pytest.fixture(
    params=[(test_echoes_data, PrimeTrilogyTeleporterConfiguration), (test_generic_data, TeleporterConfiguration)]
)
def test_decode(data, configuration):
    # Run
    decoder = BitPackDecoder(data.encoded)
    result = configuration.bit_pack_unpack(decoder, {"reference": data.reference})

    # Assert
    assert result == data.expected


@pytest.fixture(params=[test_echoes_data, test_generic_data])
def test_encode(data):
    # Setup
    value = data.expected

    # Run
    result, echoes_bit_count = bitpacking.pack_results_and_bit_count(
        value.bit_pack_encode({"reference": data.reference})
    )

    # Assert
    assert result == data.encoded


@pytest.fixture(params=[test_echoes_data, test_generic_data])
def test_description(data):
    assert data.expected.description("elevators") == data.description
