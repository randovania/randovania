import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.configuration_factory import get_major_items_configurations_for, get_ammo_configurations_for, \
    AmmoConfigEnum, MajorItemsConfigEnum
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation


class LayoutTrickLevel(BitPackEnum, Enum):
    NO_TRICKS = "no-tricks"
    TRIVIAL = "trivial"
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    HYPERMODE = "hypermode"
    MINIMAL_RESTRICTIONS = "minimal-restrictions"

    @classmethod
    def default(cls) -> "LayoutTrickLevel":
        return cls.NO_TRICKS


class LayoutSkyTempleKeyMode(BitPackEnum, Enum):
    ALL_BOSSES = "all-bosses"
    ALL_GUARDIANS = "all-guardians"
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

    @classmethod
    def default(cls) -> "LayoutSkyTempleKeyMode":
        return cls.NINE


class LayoutElevators(BitPackEnum, Enum):
    VANILLA = "vanilla"
    RANDOMIZED = "randomized"

    @classmethod
    def default(cls) -> "LayoutElevators":
        return cls.VANILLA


@dataclasses.dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level: LayoutTrickLevel
    sky_temple_keys: LayoutSkyTempleKeyMode
    elevators: LayoutElevators
    starting_location: StartingLocation
    major_items: MajorItemsConfigEnum
    ammo: AmmoConfigEnum

    @property
    def game_data(self) -> dict:
        return default_data.decode_default_prime2()

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "elevators": self.elevators.value,
            "starting_location": self.starting_location.as_json,
            "major_items": self.major_items.value,
            "ammo": self.ammo.value,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
            sky_temple_keys=LayoutSkyTempleKeyMode(json_dict["sky_temple_keys"]),
            elevators=LayoutElevators(json_dict["elevators"]),
            starting_location=StartingLocation.from_json(json_dict["starting_location"]),
            major_items=MajorItemsConfigEnum(json_dict["major_items_configuration_name"]),
            ammo=AmmoConfigEnum(json_dict["ammo_configuration_name"]),
        )

    @classmethod
    def from_params(cls, **kwargs) -> "LayoutConfiguration":
        for field in dataclasses.fields(cls):
            if field.name not in kwargs:
                kwargs[field.name] = field.type.default()
        return LayoutConfiguration(**kwargs)

    @classmethod
    def default(cls) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel.default(),
            sky_temple_keys=LayoutSkyTempleKeyMode.default(),
            elevators=LayoutElevators.default(),
            starting_location=StartingLocation.default(),
            major_items=MajorItemsConfigEnum.default(),
            ammo=AmmoConfigEnum.default(),
        )

    @property
    def major_items_configuration(self) -> MajorItemsConfiguration:
        return get_major_items_configurations_for(self.major_items)

    @property
    def ammo_configuration(self) -> AmmoConfiguration:
        return get_ammo_configurations_for(self.ammo)
