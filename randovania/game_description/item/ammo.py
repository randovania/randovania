from dataclasses import dataclass
from typing import Dict, Tuple, Optional

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import ResourceLock
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.game import RandovaniaGame


@dataclass(frozen=True, order=True)
class Ammo:
    game: RandovaniaGame
    name: str
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
    def from_json(cls, name: str, value: dict, game: RandovaniaGame,
                  item_categories: Dict[str, ItemCategory]) -> "Ammo":
        return cls(
            game=game,
            name=name,
            model_name=value["model_name"],
            items=tuple(value["items"]),
            broad_category=item_categories[value["broad_category"]],
            unlocked_by=value.get("unlocked_by"),
            temporary=value.get("temporary"),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "model_name": self.model_name,
            "items": list(self.items),
            "broad_category": self.broad_category.name,
        }
        if self.unlocked_by is not None:
            result["temporary"] = self.temporary
            result["unlocked_by"] = self.unlocked_by
        return result

    @property
    def item_category(self) -> ItemCategory:
        return AMMO_ITEM_CATEGORY

    def create_resource_lock(self, resource_database: ResourceDatabase) -> Optional[ResourceLock]:
        if self.unlocked_by is not None:
            return ResourceLock(
                locked_by=resource_database.get_item(self.unlocked_by),
                item_to_lock=resource_database.get_item(self.items[0]),
                temporary_item=resource_database.get_item(self.temporary),
            )
        return None


AMMO_ITEM_CATEGORY = ItemCategory(
    name="expansion",
    long_name="",
    hint_details=("an ", "expansion"),
    is_major=False
)
