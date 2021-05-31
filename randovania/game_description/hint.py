from dataclasses import dataclass
from enum import Enum
from typing import Optional

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.resources.pickup_index import PickupIndex


class HintType(Enum):
    # Joke
    JOKE = "joke"

    # Hints for where a set of red temple keys are
    RED_TEMPLE_KEY_SET = "red-temple-key-set"

    # All other hints
    LOCATION = "location"


class HintDarkTemple(Enum):
    AGON_WASTES = "agon-wastes"
    TORVUS_BOG = "torvus-bog"
    SANCTUARY_FORTRESS = "sanctuary-fortress"


class HintItemPrecision(Enum):
    # The exact item
    DETAILED = "detailed"

    # movement, morph ball, etc
    PRECISE_CATEGORY = "precise-category"

    # major item, key, expansion
    GENERAL_CATEGORY = "general-category"

    # x-related, life-support, or just the precise category
    BROAD_CATEGORY = "broad-category"

    # Say nothing at all about the item
    NOTHING = "nothing"


class HintLocationPrecision(Enum):
    # The exact location
    DETAILED = "detailed"

    # Includes only the world of the location
    WORLD_ONLY = "world-only"

    # Keybearer corpses
    KEYBEARER = "keybearer"

    # Amorbis, Chykka, and Quadraxis
    GUARDIAN = "guardian"

    # Vanilla Light Suit location
    LIGHT_SUIT_LOCATION = "light-suit-location"

    RELATIVE_TO_AREA = "relative-to-area"
    RELATIVE_TO_INDEX = "relative-to-index"


class HintRelativeAreaName(Enum):
    # The area's name
    NAME = "name"

    # Some unique feature of the area
    FEATURE = "feature"


@dataclass(frozen=True)
class RelativeData:
    distance_offset: Optional[int]

    @classmethod
    def from_json(cls, param: dict) -> "RelativeData":
        if "area_location" in param:
            return RelativeDataArea.from_json(param)
        else:
            return RelativeDataItem.from_json(param)


@dataclass(frozen=True)
class RelativeDataItem(JsonDataclass, RelativeData):
    other_index: PickupIndex
    precision: HintItemPrecision


@dataclass(frozen=True)
class RelativeDataArea(JsonDataclass, RelativeData):
    area_location: AreaLocation
    precision: HintRelativeAreaName


@dataclass(frozen=True)
class PrecisionPair(JsonDataclass, DataclassPostInitTypeCheck):
    location: HintLocationPrecision
    item: HintItemPrecision
    include_owner: bool
    relative: Optional[RelativeData] = None


@dataclass(frozen=True)
class Hint(JsonDataclass):
    hint_type: HintType
    precision: Optional[PrecisionPair]
    target: Optional[PickupIndex] = None
    dark_temple: Optional[HintDarkTemple] = None

    def __post_init__(self):
        if self.hint_type is HintType.JOKE:
            if self.target is not None or self.dark_temple is not None:
                raise ValueError(f"Joke Hint, but had a target or dark_temple.")
        elif self.hint_type is HintType.LOCATION:
            if self.target is None:
                raise ValueError(f"Location Hint, but no target set.")
        elif self.hint_type is HintType.RED_TEMPLE_KEY_SET:
            if self.dark_temple is None:
                raise ValueError(f"Dark Temple Hint, but no dark_temple set.")
