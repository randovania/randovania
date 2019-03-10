from dataclasses import dataclass
from typing import Dict, Iterator

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState


@dataclass(frozen=True)
class MajorItemsConfiguration(BitPackValue):
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

    def bit_pack_format(self) -> Iterator[int]:
        for item, state in self.items_state.items():
            yield from state.bit_pack_format(item)

    def bit_pack_arguments(self) -> Iterator[int]:
        for item, state in self.items_state.items():
            yield from state.bit_pack_arguments(item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "MajorItemsConfiguration":
        from randovania.game_description import default_database
        item_database = default_database.default_prime2_item_database()

        items_state = {}
        for item in item_database.major_items.values():
            items_state[item] = MajorItemState.bit_pack_unpack(decoder, item)

        return cls(items_state)

    def replace_state_for_item(self, item: MajorItem, state: MajorItemState) -> "MajorItemsConfiguration":
        return MajorItemsConfiguration(
            items_state={
                key: state if key == item else value
                for key, value in self.items_state.items()
            }
        )
