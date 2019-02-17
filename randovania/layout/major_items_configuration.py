from typing import Dict

from randovania.layout.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState


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
