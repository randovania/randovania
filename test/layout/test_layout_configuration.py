from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutSkyTempleKeyMode, \
    LayoutElevators
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
        {"encoded": b'\xb4',
         "sky_temple": LayoutSkyTempleKeyMode.NINE,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'\x04',
         "sky_temple": LayoutSkyTempleKeyMode.ALL_BOSSES,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'L',
         "sky_temple": LayoutSkyTempleKeyMode.TWO,
         "elevators": LayoutElevators.RANDOMIZED,
         },
        {"encoded": b'\x1c',
         "sky_temple": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
         "elevators": LayoutElevators.RANDOMIZED,
         },
    ],
    name="layout_config_with_data")
def _layout_config_with_data(request):
    trick_config = DummyValue()
    starting_location = DummyValue()
    major_items = DummyValue()
    ammo_config = DummyValue()
    translator_config = DummyValue()
    hints = DummyValue()

    with patch.multiple(TrickLevelConfiguration, bit_pack_unpack=MagicMock(return_value=trick_config)), \
         patch.multiple(StartingLocation, bit_pack_unpack=MagicMock(return_value=starting_location)), \
         patch.multiple(MajorItemsConfiguration, bit_pack_unpack=MagicMock(return_value=major_items)), \
         patch.multiple(AmmoConfiguration, bit_pack_unpack=MagicMock(return_value=ammo_config)), \
         patch.multiple(TranslatorConfiguration, bit_pack_unpack=MagicMock(return_value=translator_config)), \
         patch.multiple(HintConfiguration, bit_pack_unpack=MagicMock(return_value=hints)):
        yield request.param["encoded"], LayoutConfiguration.from_params(
            trick_level_configuration=trick_config,
            sky_temple_keys=request.param["sky_temple"],
            elevators=request.param["elevators"],
            starting_location=starting_location,
            major_items_configuration=major_items,
            ammo_configuration=ammo_config,
            translator_configuration=translator_config,
            hints=hints,
        )


def test_decode(layout_config_with_data):
    # Setup
    data, expected = layout_config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = LayoutConfiguration.bit_pack_unpack(decoder, {})

    # Assert
    assert result == expected


def test_encode(layout_config_with_data):
    # Setup
    expected, value = layout_config_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
