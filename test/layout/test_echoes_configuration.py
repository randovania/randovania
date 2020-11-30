import dataclasses
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.available_locations import AvailableLocationsConfiguration
from randovania.layout.beam_configuration import BeamConfiguration
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.elevators import LayoutElevators
from randovania.layout.damage_strictness import LayoutDamageStrictness
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.trick_level import TrickLevelConfiguration


@dataclass(frozen=True)
class DummyValue(BitPackValue):
    def bit_pack_encode(self, metadata):
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        raise cls()


@pytest.fixture(
    params=[
        {"encoded": b'@X=\xef\x898\x0f\x00',
         "sky_temple": LayoutSkyTempleKeyMode.NINE,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'@\x00=\xef\x898\x0f\x00',
         "sky_temple": LayoutSkyTempleKeyMode.ALL_BOSSES,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'@\xa0=\xef\x898\x0f\x00',
         "sky_temple": LayoutSkyTempleKeyMode.TWO,
         "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
         },
        {"encoded": b'@\x88=\xef\x898\x0f\x00',
         "sky_temple": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
         "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
         },
        {"encoded": b'\x00\x88=\xef\x898\x0f\x00',
         "sky_temple": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
         "elevators": LayoutElevators.TWO_WAY_RANDOMIZED,
         "damage_strictness": LayoutDamageStrictness.STRICT,
         },
    ],
    name="layout_config_with_data")
def _layout_config_with_data(request, default_layout_configuration):
    trick_config = DummyValue()
    starting_location = DummyValue()
    available_locations = DummyValue()
    major_items = DummyValue()
    ammo_config = DummyValue()
    translator_config = DummyValue()
    hints = DummyValue()
    beam_configuration = DummyValue()

    with patch.multiple(TrickLevelConfiguration, bit_pack_unpack=MagicMock(return_value=trick_config)), \
         patch.multiple(StartingLocation, bit_pack_unpack=MagicMock(return_value=starting_location)), \
         patch.multiple(AvailableLocationsConfiguration, bit_pack_unpack=MagicMock(return_value=available_locations)), \
         patch.multiple(MajorItemsConfiguration, bit_pack_unpack=MagicMock(return_value=major_items)), \
         patch.multiple(AmmoConfiguration, bit_pack_unpack=MagicMock(return_value=ammo_config)), \
         patch.multiple(TranslatorConfiguration, bit_pack_unpack=MagicMock(return_value=translator_config)), \
         patch.multiple(HintConfiguration, bit_pack_unpack=MagicMock(return_value=hints)), \
         patch.multiple(BeamConfiguration, bit_pack_unpack=MagicMock(return_value=beam_configuration)):
        yield request.param["encoded"], dataclasses.replace(
            default_layout_configuration,
            trick_level=trick_config,
            damage_strictness=request.param.get("damage_strictness", LayoutDamageStrictness.MEDIUM),
            sky_temple_keys=request.param["sky_temple"],
            elevators=request.param["elevators"],
            starting_location=starting_location,
            available_locations=available_locations,
            major_items_configuration=major_items,
            ammo_configuration=ammo_config,
            translator_configuration=translator_config,
            hints=hints,
            beam_configuration=beam_configuration,
        )


def test_decode(layout_config_with_data):
    # Setup
    data, expected = layout_config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = EchoesConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(layout_config_with_data):
    # Setup
    expected, value = layout_config_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
