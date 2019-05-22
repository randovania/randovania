import dataclasses
from enum import Enum
from typing import Tuple, Iterator, List, Dict, FrozenSet

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass, BitPackValue, BitPackDecoder
from randovania.game_description.default_database import default_prime2_item_database
from randovania.games.prime import default_data
from randovania.layout.ammo_configuration import AmmoConfiguration
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.starting_location import StartingLocation
from randovania.layout.translator_configuration import TranslatorConfiguration


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

    @classmethod
    def from_number(cls, number: int) -> "LayoutTrickLevel":
        return _TRICK_LEVEL_ORDER[number]

    @property
    def as_number(self) -> int:
        return _TRICK_LEVEL_ORDER.index(self)

    @property
    def long_name(self) -> str:
        return _PRETTY_TRICK_LEVEL_NAME[self]


_TRICK_LEVEL_ORDER: List[LayoutTrickLevel] = list(LayoutTrickLevel)

_PRETTY_TRICK_LEVEL_NAME = {
    LayoutTrickLevel.NO_TRICKS: "No Tricks",
    LayoutTrickLevel.TRIVIAL: "Trivial",
    LayoutTrickLevel.EASY: "Easy",
    LayoutTrickLevel.NORMAL: "Normal",
    LayoutTrickLevel.HARD: "Hard",
    LayoutTrickLevel.HYPERMODE: "Hypermode",
    LayoutTrickLevel.MINIMAL_RESTRICTIONS: "Minimal Checking",
}


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


class PerTrickLevelConfiguration(BitPackValue):
    values: Dict[int, LayoutTrickLevel] = {}

    @classmethod
    def default(cls):
        return cls()

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield from []

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata):
        return cls()

    def __eq__(self, other):
        # TODO: remove this
        return True

    @classmethod
    def all_possible_tricks(cls) -> FrozenSet[int]:
        return frozenset({
            0,  # Scan Dash
            1,  # Difficult Bomb Jump
            2,  # Slope Jump
            3,  # R Jump
            4,  # BSJ
            5,  # Roll Jump
            6,  # Underwater Dash
            7,  # Air Underwater
            8,  # Floaty
            9,  # Infinite Speed
            10,  # SA without SJ
            11,  # Wall Boost
            12,  # Jump off Enemy
            # 14,  # Controller Reset
            15,  # Instant Morph
        })


@dataclasses.dataclass(frozen=True)
class LayoutConfiguration(BitPackDataClass):
    global_trick_level: LayoutTrickLevel
    per_trick_level: PerTrickLevelConfiguration
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
            "trick_level": self.global_trick_level.value,
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
            global_trick_level=LayoutTrickLevel(json_dict["trick_level"]),
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
        return cls.from_params(
            global_trick_level=LayoutTrickLevel.default(),
            sky_temple_keys=LayoutSkyTempleKeyMode.default(),
            elevators=LayoutElevators.default(),
            starting_location=StartingLocation.default(),
            major_items_configuration=MajorItemsConfiguration.default(),
            ammo_configuration=AmmoConfiguration.default(),
        )
