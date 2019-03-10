from dataclasses import dataclass
from typing import Dict

from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState


@dataclass(frozen=True)
class MajorItemsConfiguration:
    items_state: Dict[MajorItem, MajorItemState]

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                major_item.name: state.as_json
                for major_item, state in self.items_state.items()
            }
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "MajorItemsConfiguration":
        return cls(
            items_state={
                item_database.major_items[name]: MajorItemState.from_json(state_data)
                for name, state_data in value["items_state"].items()
            }
        )

    def replace_state_for_item(self, item: MajorItem, state: MajorItemState) -> "MajorItemsConfiguration":
        return MajorItemsConfiguration(
            items_state={
                key: state if key == item else value
                for key, value in self.items_state.items()
            }
        )
