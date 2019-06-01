from dataclasses import dataclass
from enum import Enum
from typing import List, NamedTuple, Optional

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


class HintLocationPrecision(Enum):
    # The exact location
    DETAILED = "detailed"

    # Includes only the world of the location
    WORLD_ONLY = "world-only"

    # Something from another game entirely
    WRONG_GAME = "wrong-game"


class PrecisionPair(NamedTuple):
    location: HintLocationPrecision
    item: HintItemPrecision

    @classmethod
    def detailed(cls) -> "PrecisionPair":
        return PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED)

    @classmethod
    def joke(cls) -> "PrecisionPair":
        return PrecisionPair(HintLocationPrecision.WRONG_GAME, HintItemPrecision.WRONG_GAME)

    @classmethod
    def weighted_list(cls) -> List["PrecisionPair"]:
        tiers = {
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED): 5,
            (HintLocationPrecision.DETAILED, HintItemPrecision.PRECISE_CATEGORY): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.GENERAL_CATEGORY): 1,

            (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.DETAILED): 2,
            (HintLocationPrecision.WORLD_ONLY, HintItemPrecision.PRECISE_CATEGORY): 1,

            (HintLocationPrecision.DETAILED, HintItemPrecision.WRONG_GAME): 1,
            (HintLocationPrecision.WRONG_GAME, HintItemPrecision.WRONG_GAME): 1,
        }

        hints = []
        for params, quantity in tiers.items():
            hints.extend([PrecisionPair(*params)] * quantity)

        return hints

    @property
    def is_joke(self) -> bool:
        return self == PrecisionPair.joke()


@dataclass(frozen=True)
class Hint:
    hint_type: HintType
    precision: Optional[PrecisionPair]
    target: PickupIndex

    @property
    def location_precision(self) -> HintLocationPrecision:
        return self.precision.location

    @property
    def item_precision(self) -> HintItemPrecision:
        return self.precision.item

    @property
    def as_json(self):
        return {
            "location_precision": self.precision.location.value,
            "item_precision": self.precision.item.value,
            "target": self.target.index,
        }

    @classmethod
    def from_json(cls, value) -> "Hint":
        return Hint(
            hint_type=HintType.LOCATION,
            precision=PrecisionPair(
                location=HintLocationPrecision(value["location_precision"]),
                item=HintItemPrecision(value["item_precision"]),
            ),
            target=PickupIndex(value["target"]),
        )
