from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import List

from randovania.game_description.resources.pickup_index import PickupIndex


class HintType(Enum):
    LOCATION = "location"


class HintItemPrecision(Enum):
    # The exact item
    DETAILED = "detailed"

    # movement, morph ball, etc
    PRECISE_CATEGORY = "precise-category"

    # major item, key, expansion
    GENERAL_CATEGORY = "general-category"

    # Something from another game entirely
    WRONG_GAME = "wrong-game"

    @classmethod
    def weighted_list(cls) -> List["HintItemPrecision"]:
        return [cls.DETAILED, cls.DETAILED, cls.PRECISE_CATEGORY, cls.GENERAL_CATEGORY, cls.WRONG_GAME]


class HintLocationPrecision(Enum):
    # The exact location
    DETAILED = "detailed"

    # Includes only the world of the location
    WORLD_ONLY = "world-only"

    # Something from another game entirely
    WRONG_GAME = "wrong-game"

    @classmethod
    def weighted_list(cls) -> List["HintLocationPrecision"]:
        return [cls.DETAILED, cls.DETAILED, cls.DETAILED, cls.WORLD_ONLY, cls.WRONG_GAME]


@dataclass(frozen=True)
class Hint:
    hint_type: HintType
    location_precision: HintLocationPrecision
    item_precision: HintItemPrecision
    target: PickupIndex

    @property
    def as_json(self):
        return {
            "location_precision": self.location_precision.value,
            "item_precision": self.item_precision.value,
            "target": self.target.index,
        }

    @classmethod
    def from_json(cls, value) -> "Hint":
        return Hint(
            hint_type=HintType.LOCATION,
            location_precision=HintLocationPrecision(value["location_precision"]),
            item_precision=HintItemPrecision(value["item_precision"]),
            target=PickupIndex(value["target"]),
        )
