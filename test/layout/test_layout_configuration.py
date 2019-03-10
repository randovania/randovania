from dataclasses import dataclass
from unittest.mock import patch, MagicMock

import pytest

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutSkyTempleKeyMode, \
    LayoutElevators
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation


@dataclass(frozen=True)
class DummyValue(BitPackValue):
    def bit_pack_format(self):
        yield from []

    def bit_pack_arguments(self):
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder):
        raise cls()


@pytest.fixture(
    params=[
        {"encoded": b'\x16',
         "trick": LayoutTrickLevel.NO_TRICKS,
         "sky_temple": LayoutSkyTempleKeyMode.NINE,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'\xa0',
         "trick": LayoutTrickLevel.HYPERMODE,
         "sky_temple": LayoutSkyTempleKeyMode.ALL_BOSSES,
         "elevators": LayoutElevators.VANILLA,
         },
        {"encoded": b'\x89',
         "trick": LayoutTrickLevel.HARD,
         "sky_temple": LayoutSkyTempleKeyMode.TWO,
         "elevators": LayoutElevators.RANDOMIZED,
         },
        {"encoded": b'\xc3',
         "trick": LayoutTrickLevel.MINIMAL_RESTRICTIONS,
         "sky_temple": LayoutSkyTempleKeyMode.ALL_GUARDIANS,
         "elevators": LayoutElevators.RANDOMIZED,
         },
    ],
    name="layout_config_with_data")
def _layout_config_with_data(request):
    starting_location = DummyValue()
    major_items = DummyValue()
    ammo_config = DummyValue()

    with patch.multiple(StartingLocation, bit_pack_unpack=MagicMock(return_value=starting_location)), \
         patch.multiple(MajorItemsConfiguration, bit_pack_unpack=MagicMock(return_value=major_items)), \
         patch.multiple(AmmoConfiguration, bit_pack_unpack=MagicMock(return_value=ammo_config)):
        yield request.param["encoded"], LayoutConfiguration.from_params(
            trick_level=request.param["trick"],
            sky_temple_keys=request.param["sky_temple"],
            elevators=request.param["elevators"],
            starting_location=starting_location,
            major_items_configuration=major_items,
            ammo_configuration=ammo_config,
        )


def test_decode(layout_config_with_data):
    # Setup
    data, expected = layout_config_with_data

    # Run
    decoder = BitPackDecoder(data)
    result = LayoutConfiguration.bit_pack_unpack(decoder)

    # Assert
    assert result == expected


def test_encode(layout_config_with_data):
    # Setup
    expected, value = layout_config_with_data

    # Run
    result = bitpacking.pack_value(value)

    # Assert
    assert result == expected
