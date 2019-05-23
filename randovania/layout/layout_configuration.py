import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.default_database import default_prime2_item_database
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.trick_level import TrickLevelConfiguration


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
    RANDOMIZED = "randomized"

    @classmethod
    def default(cls) -> "LayoutElevators":
        return cls.VANILLA


@dataclasses.dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    trick_level_configuration: TrickLevelConfiguration
    sky_temple_keys: LayoutSkyTempleKeyMode
    elevators: LayoutElevators
    starting_location: StartingLocation
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    translator_configuration: TranslatorConfiguration
    hints: HintConfiguration
    # FIXME: Most of the following should go in MajorItemsConfiguration/AmmoConfiguration
    split_beam_ammo: bool = True

    @property
    def game_data(self) -> dict:
        return default_data.decode_default_prime2()

    @property
    def as_json(self) -> dict:
        return {
            "game": "mp2-echoes",
            "trick_level": self.trick_level_configuration.as_json,
            "sky_temple_keys": self.sky_temple_keys.value,
            "elevators": self.elevators.value,
            "starting_location": self.starting_location.as_json,
            "major_items_configuration": self.major_items_configuration.as_json,
            "ammo_configuration": self.ammo_configuration.as_json,
            "translator_configuration": self.translator_configuration.as_json,
            "hints": self.hints.as_json,
            "split_beam_ammo": self.split_beam_ammo,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level_configuration=TrickLevelConfiguration.from_json(json_dict["trick_level"]),
            sky_temple_keys=LayoutSkyTempleKeyMode(json_dict["sky_temple_keys"]),
            elevators=LayoutElevators(json_dict["elevators"]),
            starting_location=StartingLocation.from_json(json_dict["starting_location"]),
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

    @classmethod
    def from_params(cls, **kwargs) -> "LayoutConfiguration":
        for field in dataclasses.fields(cls):
            if field.name not in kwargs:
                if field.default is dataclasses.MISSING:
                    kwargs[field.name] = field.type.default()
        return LayoutConfiguration(**kwargs)

    @classmethod
    def default(cls) -> "LayoutConfiguration":
        return cls.from_params()
