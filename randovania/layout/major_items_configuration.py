import copy
from dataclasses import dataclass
from typing import Dict, Iterator, Tuple, List

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

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        default = MajorItemsConfiguration.default()

        result: List[Tuple[int, MajorItem, MajorItemState]] = []
        for i, (item, state) in enumerate(self.items_state.items()):
            if state != default.items_state[item]:
                result.append((i, item, state))

        yield len(result), len(self.items_state)
        for index, _, _ in result:
            yield index, len(self.items_state)

        for index, item, state in result:
            yield from state.bit_pack_encode(item)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder) -> "MajorItemsConfiguration":
        from randovania.game_description import default_database
        item_database = default_database.default_prime2_item_database()

        default = MajorItemsConfiguration.default()
        num_items = decoder.decode_single(len(default.items_state))
        indices_with_custom = {
            decoder.decode_single(len(default.items_state))
            for _ in range(num_items)
        }

        items_state = {}

        for index, item in enumerate(item_database.major_items.values()):
            if index in indices_with_custom:
                items_state[item] = MajorItemState.bit_pack_unpack(decoder, item)
            else:
                items_state[item] = default.items_state[item]

        return cls(items_state)

    def replace_state_for_item(self, item: MajorItem, state: MajorItemState) -> "MajorItemsConfiguration":
        return self.replace_states({
            item: state
        })

    def replace_states(self, new_states: Dict[MajorItem, MajorItemState]) -> "MajorItemsConfiguration":
        """
        Creates a copy of this MajorItemsConfiguration where the state of all given items are replaced by the given
        states.
        :param new_states:
        :return:
        """
        items_state = copy.copy(self.items_state)

        for item, state in new_states.items():
            items_state[item] = state

        return MajorItemsConfiguration(items_state)

    @classmethod
    def default(cls):
        from randovania.layout import configuration_factory
        return configuration_factory.get_major_items_configurations_for(
            configuration_factory.MajorItemsConfigEnum.default())
