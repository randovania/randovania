from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TypeVar
from unittest.mock import MagicMock, patch

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
)
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.beam_configuration import BeamConfiguration
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.games.prime2.layout.hint_configuration import HintConfiguration
from randovania.games.prime2.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.dock_rando_configuration import DockRandoConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration

T = TypeVar("T")


@dataclass(frozen=True)
class DummyValue(BitPackValue):
    def bit_pack_encode(self, metadata):
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        raise cls


def empty_bit_pack_encode(*args):
    yield from []


@contextlib.contextmanager
def make_dummy(cls: type[T]) -> T:
    m = MagicMock(spec=cls)
    m.bit_pack_encode = empty_bit_pack_encode
    m.as_json = m

    ret = MagicMock(return_value=m)
    with patch.multiple(cls, from_json=ret, bit_pack_unpack=ret, as_json=ret):
        yield m


@pytest.fixture(
    params=[
        {
            "encoded": b"@\x00\x1a\xc6?\x8b\x86\x02X\x01\xff",
            "sky_temple_keys": LayoutSkyTempleKeyMode.NINE.value,
        },
        {
            "encoded": b"@\x00\x18\x06?\x8b\x86\x02X\x01\xff",
            "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_BOSSES.value,
        },
        {
            "encoded": b"@\x00\x19\x11\x7f\x8b\x86\x02X\x01\xff",
            "sky_temple_keys": LayoutSkyTempleKeyMode.TWO.value,
            "energy_per_tank": 280,
        },
        {
            "encoded": b"@\x00\x18F?\xa2\xf6\x02X\x01\xff",
            "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS.value,
            "varia_suit_damage": 18.0,
        },
        {
            "encoded": b"\x10\x00\x18F?\x8b\x86\x02X\x01\xff",
            "pickup_model_style": PickupModelStyle.HIDE_MODEL.value,
            "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS.value,
            "damage_strictness": LayoutDamageStrictness.STRICT.value,
        },
    ],
)
def layout_config_with_data(request, default_echoes_configuration):
    data = default_echoes_configuration.as_json
    for key, value in request.param.items():
        if key != "encoded":
            assert key in data
            data[key] = value

    types_to_mock = {
        "trick_level": TrickLevelConfiguration,
        "starting_location": StartingLocationList,
        "available_locations": AvailableLocationsConfiguration,
        "standard_pickup_configuration": StandardPickupConfiguration,
        "ammo_pickup_configuration": AmmoPickupConfiguration,
        "teleporters": PrimeTrilogyTeleporterConfiguration,
        "translator_configuration": TranslatorConfiguration,
        "hints": HintConfiguration,
        "beam_configuration": BeamConfiguration,
        "dock_rando": DockRandoConfiguration,
    }

    with contextlib.ExitStack() as stack:
        for key, cls in types_to_mock.items():
            assert key in data
            data[key] = stack.enter_context(make_dummy(cls))
        yield (
            request.param["encoded"],
            EchoesConfiguration.from_json(data, game=RandovaniaGame.METROID_PRIME_ECHOES),
            data,
        )


def test_decode(layout_config_with_data):
    # Setup
    data, expected, _ = layout_config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = EchoesConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(layout_config_with_data):
    # Setup
    expected, value, expected_json = layout_config_with_data

    # Run
    result = bitpacking.pack_value(value)
    as_json = value.as_json

    # Assert
    assert result == expected
    assert as_json == expected_json
