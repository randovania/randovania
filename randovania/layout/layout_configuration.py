import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.default_database import default_prime2_item_database
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.available_locations import AvailableLocationsConfiguration, RandomizationMode
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.trick_level import TrickLevelConfiguration


class LayoutDamageStrictness(BitPackEnum, Enum):
    STRICT = 1.0
    MEDIUM = 1.5
    LENIENT = 2.0

    @classmethod
    def default(cls):
        return cls.MEDIUM

    @property
    def long_name(self) -> str:
        if self == LayoutDamageStrictness.STRICT:
            return "Strict"
        elif self == LayoutDamageStrictness.MEDIUM:
            return "Medium"
        elif self == LayoutDamageStrictness.LENIENT:
            return "Lenient"
        else:
            return "Custom"


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

    @property
    def num_keys(self):
        if self == self.ALL_BOSSES:
            return 9
        elif self == self.ALL_GUARDIANS:
            return 3
        else:
            return self.value


class LayoutElevators(BitPackEnum, Enum):
    VANILLA = "vanilla"
    TWO_WAY_RANDOMIZED = "randomized"
    TWO_WAY_UNCHECKED = "two-way-unchecked"
    ONE_WAY_ELEVATOR = "one-way-elevator"
    ONE_WAY_ANYTHING = "one-way-anything"

    @classmethod
    def default(cls) -> "LayoutElevators":
        return cls.VANILLA


@dataclasses.dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level_configuration: TrickLevelConfiguration
    damage_strictness: LayoutDamageStrictness
    sky_temple_keys: LayoutSkyTempleKeyMode
    elevators: LayoutElevators
    starting_location: StartingLocation
    available_locations: AvailableLocationsConfiguration
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    translator_configuration: TranslatorConfiguration
    hints: HintConfiguration
    # FIXME: Most of the following should go in MajorItemsConfiguration/AmmoConfiguration
    split_beam_ammo: bool = True

    @property
    def randomization_mode(self) -> RandomizationMode:
        return self.available_locations.randomization_mode

    @property
    def game_data(self) -> dict:
        return default_data.decode_default_prime2()

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level_configuration.as_json,
            "damage_strictness": self.damage_strictness.value,
            "sky_temple_keys": self.sky_temple_keys.value,
            "elevators": self.elevators.value,
            "starting_location": self.starting_location.as_json,
            "available_locations": self.available_locations.as_json,
            "major_items_configuration": self.major_items_configuration.as_json,
            "ammo_configuration": self.ammo_configuration.as_json,
            "translator_configuration": self.translator_configuration.as_json,
            "hints": self.hints.as_json,
            "split_beam_ammo": self.split_beam_ammo,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return LayoutConfiguration(
            trick_level_configuration=TrickLevelConfiguration.from_json(json_dict["trick_level"]),
            damage_strictness=LayoutDamageStrictness(json_dict["damage_strictness"]),
            sky_temple_keys=LayoutSkyTempleKeyMode(json_dict["sky_temple_keys"]),
            elevators=LayoutElevators(json_dict["elevators"]),
            starting_location=StartingLocation.from_json(json_dict["starting_location"]),
            available_locations=AvailableLocationsConfiguration.from_json(json_dict["available_locations"]),
            major_items_configuration=MajorItemsConfiguration.from_json(
                json_dict["major_items_configuration"],
                default_prime2_item_database(),
            ),
            ammo_configuration=AmmoConfiguration.from_json(
                json_dict["ammo_configuration"],
                default_prime2_item_database(),
            ),
            translator_configuration=TranslatorConfiguration.from_json(json_dict["translator_configuration"]),
            hints=HintConfiguration.from_json(json_dict["hints"]),
            split_beam_ammo=json_dict["split_beam_ammo"],
        )
