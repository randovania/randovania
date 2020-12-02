from dataclasses import dataclass
from typing import Tuple, Optional

from randovania.game_description.item.item_category import ItemCategory


@dataclass(frozen=True, order=True)
class Ammo:
    name: str
    maximum: int
    items: Tuple[int, ...]
    broad_category: ItemCategory
    unlocked_by: Optional[int] = None
    temporaries: Tuple[int, ...] = tuple()
    models: Tuple[int, ...] = tuple()

    def __post_init__(self):
        if self.temporaries:
            if self.unlocked_by is None:
                raise ValueError("If temporaries is not empty, unlocked_by must be set.")
            if len(self.temporaries) != len(self.items):
                raise ValueError("If non-empty, temporaries must have the same size of items. Got {0} and {1}".format(
                    len(self.temporaries), len(self.items)
                ))
        elif self.unlocked_by is not None:
            raise ValueError("If temporaries is empty, unlocked_by must not be set.")

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            maximum=value["maximum"],
            models=tuple(value["models"]),
            items=tuple(value["items"]),
            broad_category=ItemCategory(value["broad_category"]),
            unlocked_by=value.get("unlocked_by"),
            temporaries=tuple(value.get("temporaries", [])),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "maximum": self.maximum,
            "models": list(self.models),
            "items": list(self.items),
            "broad_category": self.broad_category.value,
            "temporaries": list(self.temporaries),
        }
        if self.unlocked_by is not None:
            result["unlocked_by"] = self.unlocked_by
        return result

    @property
    def model_index(self):
        return self.models[0]
