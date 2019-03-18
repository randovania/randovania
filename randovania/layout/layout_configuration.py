import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.game_description.default_database import default_prime2_item_database
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
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
    major_items_configuration: MajorItemsConfiguration
    ammo_configuration: AmmoConfiguration
    # FIXME: Most of the following should go in MajorItemsConfiguration/AmmoConfiguration
    split_beam_ammo: bool = True
    missile_launcher_required: bool = True
    main_power_bombs_required: bool = True

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
            "major_items_configuration": self.major_items_configuration.as_json,
            "ammo_configuration": self.ammo_configuration.as_json,
            "split_beam_ammo": self.split_beam_ammo,
            "missile_launcher_required": self.missile_launcher_required,
            "main_power_bombs_required": self.main_power_bombs_required,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutConfiguration":
        return cls.from_params(
            trick_level=LayoutTrickLevel(json_dict["trick_level"]),
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
            split_beam_ammo=json_dict["split_beam_ammo"],
            missile_launcher_required=json_dict["missile_launcher_required"],
            main_power_bombs_required=json_dict["main_power_bombs_required"],
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
        return cls.from_params(
            trick_level=LayoutTrickLevel.default(),
            sky_temple_keys=LayoutSkyTempleKeyMode.default(),
            elevators=LayoutElevators.default(),
            starting_location=StartingLocation.default(),
            major_items_configuration=MajorItemsConfiguration.default(),
            ammo_configuration=AmmoConfiguration.default(),
        )
