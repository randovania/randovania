from dataclasses import dataclass
from typing import Tuple, Optional

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import ResourceLock
from randovania.game_description.resources.resource_database import ResourceDatabase


@dataclass(frozen=True, order=True)
class Ammo:
    name: str
    maximum: int
    model_name: str
    items: Tuple[int, ...]
    broad_category: ItemCategory
    unlocked_by: Optional[int] = None
    temporary: Optional[int] = None

    def __post_init__(self):
        if self.temporary is not None:
            if self.unlocked_by is None:
                raise ValueError("If temporaries is set, unlocked_by must be set.")
            if len(self.items) != 1:
                raise ValueError("If temporaries is set, only one item is supported. Got {0} instead".format(
                    len(self.items)
                ))
        elif self.unlocked_by is not None:
            raise ValueError("If temporaries is not set, unlocked_by must not be set.")

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            maximum=value["maximum"],
            model_name=value["model_name"],
            items=tuple(value["items"]),
            broad_category=ItemCategory(value["broad_category"]),
            unlocked_by=value.get("unlocked_by"),
            temporary=value.get("temporary"),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "maximum": self.maximum,
            "model_name": self.model_name,
            "items": list(self.items),
            "broad_category": self.broad_category.value,
        }
        if self.unlocked_by is not None:
            result["temporary"] = self.temporary
            result["unlocked_by"] = self.unlocked_by
        return result

    def create_resource_lock(self, resource_database: ResourceDatabase) -> Optional[ResourceLock]:
        if self.unlocked_by is not None:
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None
