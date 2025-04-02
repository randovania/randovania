from __future__ import annotations

import dataclasses
import typing
from typing import TYPE_CHECKING, NamedTuple, Self

from randovania.game_description.resources.resource_type import ResourceType

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceGain


class InventoryItem(NamedTuple):
    amount: int
    capacity: int


@dataclasses.dataclass(frozen=True, slots=True)
class Inventory:
    raw: dict[ItemResourceInfo, InventoryItem]

    @classmethod
    def empty(cls) -> Self:
        return cls({})

    @classmethod
    def from_collection(cls, collection: ResourceCollection) -> Self:
        return cls(
            {
                typing.cast("ItemResourceInfo", resource): InventoryItem(quantity, quantity)
                for resource, quantity in collection.as_resource_gain()
                if resource.resource_type == ResourceType.ITEM
            }
        )

    def __setitem__(self, key: ItemResourceInfo, value: InventoryItem) -> None:
        self.raw[key] = value

    def __getitem__(self, item: ItemResourceInfo) -> InventoryItem:
        return self.raw[item]

    def get(self, key: ItemResourceInfo) -> InventoryItem:
        return self.raw.get(key, InventoryItem(0, 0))

    def as_resource_gain(self) -> ResourceGain:
        for info, item in self.raw.items():
            yield info, item.capacity
