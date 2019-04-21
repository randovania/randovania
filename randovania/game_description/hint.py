from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Union

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class HintType(Enum):
    LOCATION = "location"
    ITEM = "item"


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
    def random(cls, rng: Random) -> "HintItemPrecision":
        return rng.choice([cls.DETAILED, cls.DETAILED, cls.PRECISE_CATEGORY, cls.GENERAL_CATEGORY, cls.WRONG_GAME])


class HintLocationPrecision(Enum):
    # The exact location
    DETAILED = "detailed"

    # Includes only the world of the location
    WORLD_ONLY = "world-only"

    # Something from another game entirely
    WRONG_GAME = "wrong-game"

    @classmethod
    def random(cls, rng: Random) -> "HintLocationPrecision":
        return rng.choice([cls.DETAILED, cls.DETAILED, cls.DETAILED, cls.WORLD_ONLY, cls.WRONG_GAME])


@dataclass(frozen=True)
class Hint:
    hint_type: HintType
    location_precision: HintLocationPrecision
    item_precision: HintItemPrecision
    target: Union[PickupIndex, SimpleResourceInfo]
