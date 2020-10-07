from dataclasses import dataclass
from enum import Enum
from typing import List, NamedTuple, Optional

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


class PrecisionPair(NamedTuple):
    location: HintLocationPrecision
    item: HintItemPrecision

    @property
    def as_json(self):
        return {
            "location": self.location.value,
            "item": self.item.value,
        }

    @classmethod
    def from_json(cls, param) -> Optional["PrecisionPair"]:
        if param is None:
            return None
        return PrecisionPair(
            location=HintLocationPrecision(param["location"]),
            item=HintItemPrecision(param["item"]),
        )


@dataclass(frozen=True)
class Hint:
    hint_type: HintType
    precision: Optional[PrecisionPair]
    target: Optional[PickupIndex]

    def __post_init__(self):
        if self.target is None and self.hint_type != HintType.JOKE:
            raise ValueError(f"Hint with None target, but not properly a joke.")

    @property
    def item_precision(self) -> HintItemPrecision:
        return self.precision.item

    @property
    def as_json(self):
        return {
            "hint_type": self.hint_type.value,
            "precision": self.precision.as_json if self.precision is not None else None,
            "target": self.target.index if self.target is not None else None,
        }

    @classmethod
    def from_json(cls, value) -> "Hint":
        return Hint(
            hint_type=HintType(value["hint_type"]),
            precision=PrecisionPair.from_json(value["precision"]),
            target=PickupIndex(value["target"]) if value["target"] is not None else None,
        )
