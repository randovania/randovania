import copy
import dataclasses
from typing import Dict, Iterator, Tuple, List

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState

RANDOM_STARTING_ITEMS_LIMIT = 31


@dataclasses.dataclass(frozen=True)
class MajorItemsConfiguration(BitPackValue):
    items_state: Dict[MajorItem, MajorItemState]
    minimum_random_starting_items: int
    maximum_random_starting_items: int

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                major_item.name: state.as_json
                for major_item, state in self.items_state.items()
            },
            "minimum_random_starting_items": self.minimum_random_starting_items,
            "maximum_random_starting_items": self.maximum_random_starting_items,
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "MajorItemsConfiguration":
        items_state = {}
        for name, item in item_database.major_items.items():
            if name in value["items_state"]:
                state = MajorItemState.from_json(value["items_state"][name])
            else:
                state = MajorItemState()
            items_state[item] = state

        return cls(
            items_state=items_state,
            minimum_random_starting_items=value["minimum_random_starting_items"],
            maximum_random_starting_items=value["maximum_random_starting_items"],
        )

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        reference: MajorItemsConfiguration = metadata["reference"]

        result: List[Tuple[int, MajorItem, MajorItemState]] = []
        for i, (item, state) in enumerate(self.items_state.items()):
            if state != reference.items_state[item]:
                result.append((i, item, state))

        yield len(result), len(self.items_state)
        for index, _, _ in result:
            yield index, len(self.items_state)

        for index, item, state in result:
            yield from state.bit_pack_encode(item)

        yield self.minimum_random_starting_items, RANDOM_STARTING_ITEMS_LIMIT
        yield self.maximum_random_starting_items, RANDOM_STARTING_ITEMS_LIMIT

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "MajorItemsConfiguration":
        reference: MajorItemsConfiguration = metadata["reference"]

        num_items = decoder.decode_single(len(reference.items_state))
        indices_with_custom = {
            decoder.decode_single(len(reference.items_state))
            for _ in range(num_items)
        }

        items_state = {}

        for index, item in enumerate(reference.items_state.keys()):
            if index in indices_with_custom:
                items_state[item] = MajorItemState.bit_pack_unpack(decoder, item)
            else:
                items_state[item] = reference.items_state[item]

        minimum, maximum = decoder.decode(RANDOM_STARTING_ITEMS_LIMIT, RANDOM_STARTING_ITEMS_LIMIT)

        return cls(items_state,
                   minimum_random_starting_items=minimum,
                   maximum_random_starting_items=maximum)

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

        return dataclasses.replace(self, items_state=items_state)

    def calculate_provided_ammo(self) -> Dict[int, int]:
        result: Dict[int, int] = {}

        for item, state in self.items_state.items():
            total_pickups = state.num_shuffled_pickups + state.num_included_in_starting_items
            if state.include_copy_in_original_location:
                total_pickups += 1

            for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo):
                result[ammo_index] = result.get(ammo_index, 0) + ammo_count * total_pickups

        return result

    def dangerous_settings(self) -> List[str]:
        result = []
        for major_item, state in self.items_state.items():
            if (major_item.warning is not None and "EXPERIMENTAL" in major_item.warning
                    and state.num_included_in_starting_items == 0):
                result.append(f"Not starting with {major_item.name}")

        return result
