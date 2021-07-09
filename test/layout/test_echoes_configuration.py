import contextlib
from dataclasses import dataclass
from typing import TypeVar, Type
from unittest.mock import patch, MagicMock

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.games.game import RandovaniaGame
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import AvailableLocationsConfiguration
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.prime2.beam_configuration import BeamConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.prime2.hint_configuration import HintConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.lib.teleporters import TeleporterConfiguration
from randovania.layout.prime2.translator_configuration import TranslatorConfiguration
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration

T = TypeVar("T")


@dataclass(frozen=True)
class DummyValue(BitPackValue):
    def bit_pack_encode(self, metadata):
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        raise cls()


def empty_bit_pack_encode(*args):
    yield from []


@contextlib.contextmanager
def make_dummy(cls: Type[T]) -> T:
    m = MagicMock(spec=cls)
    m.bit_pack_encode = empty_bit_pack_encode
    m.as_json = m

    ret = MagicMock(return_value=m)
    with patch.multiple(cls, from_json=ret, bit_pack_unpack=ret, as_json=ret):
        yield m


@pytest.fixture(
    params=[
        {"encoded": b'Ac\x1f\xc5\xc3\x01,\x0f\xf8',
         "sky_temple_keys": LayoutSkyTempleKeyMode.NINE.value,
         },
        {"encoded": b'@\x03\x1f\xc5\xc3\x01,\x0f\xf8',
         "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_BOSSES.value,
         },
        {"encoded": b'@\x88\xbf\xc5\xc3\x01,\x0f\xf8',
         "sky_temple_keys": LayoutSkyTempleKeyMode.TWO.value,
         "energy_per_tank": 280,
         },
        {"encoded": b'@#\x1f\xd1{\x01,\x0f\xf8',
         "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS.value,
         "varia_suit_damage": 18.0,
         },
        {"encoded": b'\x10#\x1f\xc5\xc3\x01,\x0f\xf8',
         "pickup_model_style": PickupModelStyle.HIDE_MODEL.value,
         "sky_temple_keys": LayoutSkyTempleKeyMode.ALL_GUARDIANS.value,
         "damage_strictness": LayoutDamageStrictness.STRICT.value,
         },
    ],
    name="layout_config_with_data")
def _layout_config_with_data(request, default_layout_configuration):
    data = default_layout_configuration.as_json
    for key, value in request.param.items():
        if key != "encoded":
            assert key in data
            data[key] = value

    types_to_mock = {
        "trick_level": TrickLevelConfiguration,
        "starting_location": StartingLocationList,
        "available_locations": AvailableLocationsConfiguration,
        "major_items_configuration": MajorItemsConfiguration,
        "ammo_configuration": AmmoConfiguration,

        "elevators": TeleporterConfiguration,
        "translator_configuration": TranslatorConfiguration,
        "hints": HintConfiguration,
        "beam_configuration": BeamConfiguration,
    }

    with contextlib.ExitStack() as stack:
        for key, cls in types_to_mock.items():
            assert key in data
            data[key] = stack.enter_context(make_dummy(cls))
        yield request.param["encoded"], EchoesConfiguration.from_json(data, game=RandovaniaGame.METROID_PRIME_ECHOES), data


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
