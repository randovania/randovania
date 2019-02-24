from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Tuple


class MajorItemCategory(Enum):
    VISOR = "visor"
    SUIT = "suit"
    BEAM = "beam"
    MORPH_BALL = "morph_ball"
    MOVEMENT = "movement"
    MISSILE = "missile"
    BEAM_COMBO = "beam_combo"
    TRANSLATOR = "translator"


@dataclass(frozen=True)
class MajorItem:
    name: str
    item_category: MajorItemCategory
    model_index: int
    item: int
    ammo: Tuple[int, ...]
    required: bool
    original_index: Optional[int]
    probability_offset: int

    @classmethod
    def from_json(cls, name: str, value: dict) -> "MajorItem":
        return cls(
            name=name,
            item_category=MajorItemCategory(value["item_category"]),
            model_index=value["model_index"],
            item=value["item"],
            ammo=tuple(value.get("ammo", [])),
            required=value.get("required", False),
            original_index=value.get("original_index"),
            probability_offset=value["probability_offset"],
        )

    @property
    def as_json(self) -> dict:
        return {
            "item_category": self.item_category.value,
            "model_index": self.model_index,
            "item": self.item,
            "ammo": list(self.ammo),
            "required": self.required,
            "original_index": self.original_index,
            "probability_offset": self.probability_offset,
        }
