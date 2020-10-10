from dataclasses import dataclass
from enum import Enum
from typing import Optional

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.resources.pickup_index import PickupIndex


class HintType(Enum):
    # Joke
    JOKE = "joke"

    # All other hints
    LOCATION = "location"


class HintItemPrecision(Enum):
    # The exact item
    DETAILED = "detailed"

    # movement, morph ball, etc
    PRECISE_CATEGORY = "precise-category"

    # major item, key, expansion
    GENERAL_CATEGORY = "general-category"


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
    precise_distance: bool

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
class PrecisionPair(JsonDataclass):
    location: HintLocationPrecision
    item: HintItemPrecision
    relative: Optional[RelativeData] = None


@dataclass(frozen=True)
class Hint(JsonDataclass):
    hint_type: HintType
    precision: Optional[PrecisionPair]
    target: Optional[PickupIndex]

    def __post_init__(self):
        if self.target is None and self.hint_type != HintType.JOKE:
            raise ValueError(f"Hint with None target, but not properly a joke.")
