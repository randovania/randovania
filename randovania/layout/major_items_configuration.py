from dataclasses import dataclass
from typing import Dict

from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState


@dataclass(frozen=True)
class MajorItemsConfiguration:
    items_state: Dict[MajorItem, MajorItemState]
    ammo_count_for_item: Dict[MajorItem, int]
    progressive_suit: bool

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                major_item.name: state.value
                for major_item, state in self.items_state.items()
            },
            "ammo_count": {
                major_item.name: count
                for major_item, count in self.ammo_count_for_item.items()
            },
            "progressive_suit": self.progressive_suit,
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "MajorItemsConfiguration":
        return cls(
            items_state={
                item_database.major_items[name]: MajorItemState(state)
                for name, state in value["items_state"].items()
            },
            ammo_count_for_item={
                item_database.major_items[name]: count
                for name, count in value["ammo_count"].items()
            },
            progressive_suit=value["progressive_suit"]
        )

    @classmethod
    def default(cls) -> "MajorItemsConfiguration":
        return cls(
            items_state={},
            ammo_count_for_item={},
            progressive_suit=True
        )
