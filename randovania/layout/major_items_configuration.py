import copy
import dataclasses
from typing import Dict, Iterator, Tuple, List

from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description.item.item_database import ItemDatabase
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.major_item_state import MajorItemState


@dataclasses.dataclass(frozen=True)
class MajorItemsConfiguration(BitPackValue):
    items_state: Dict[MajorItem, MajorItemState]
    progressive_suit: bool = True
    progressive_grapple: bool = True

    @property
    def as_json(self) -> dict:
        default = MajorItemsConfiguration.default()
        return {
            "items_state": {
                major_item.name: state.as_json
                for major_item, state in self.items_state.items()
                if state != default.items_state[major_item]
            },
            "progressive_suit": self.progressive_suit,
            "progressive_grapple": self.progressive_grapple,
        }

    @classmethod
    def from_json(cls, value: dict, item_database: ItemDatabase) -> "MajorItemsConfiguration":
        default = cls.default()

        items_state = copy.copy(default.items_state)
        for name, state_data in value["items_state"].items():
            items_state[item_database.major_items[name]] = MajorItemState.from_json(state_data)

        return cls(
            items_state=items_state,
            progressive_suit=value["progressive_suit"],
            progressive_grapple=value["progressive_grapple"],
        )

    def bit_pack_encode(self) -> Iterator[Tuple[int, int]]:
        yield int(self.progressive_suit), 2
        yield int(self.progressive_grapple), 2
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

        progressive_suit, progressive_grapple = decoder.decode(2, 2)

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

        return cls(items_state,
                   progressive_suit=bool(progressive_suit),
                   progressive_grapple=bool(progressive_grapple))

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

    @classmethod
    def default(cls):
        from randovania.layout import configuration_factory
        return configuration_factory.get_default_major_items_configurations()

    def calculate_provided_ammo(self) -> Dict[int, int]:
        result: Dict[int, int] = {}

        for item, state in self.items_state.items():
            total_pickups = state.num_shuffled_pickups + state.num_included_in_starting_items
            if state.include_copy_in_original_location:
                total_pickups += 1

            for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo):
                result[ammo_index] = result.get(ammo_index, 0) + ammo_count * total_pickups

        return result
