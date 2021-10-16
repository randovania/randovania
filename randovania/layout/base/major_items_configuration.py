import copy
import dataclasses
from typing import Dict, Iterator, Tuple, List, TypeVar, Iterable

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.game_description import default_database
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame
from randovania.layout.base.major_item_state import MajorItemState

T = TypeVar("T")


def _check_matching_items(actual: Iterable[T], reference: Iterable[T]):
    actual_items = set(actual)
    reference_items = set(reference)
    if actual_items != reference_items:
        raise ValueError(f"Non-matching keys: Has {actual_items}, expected {reference_items}.")


@dataclasses.dataclass(frozen=True)
class MajorItemsConfiguration(BitPackValue):
    game: RandovaniaGame
    items_state: Dict[MajorItem, MajorItemState]
    default_items: Dict[ItemCategory, MajorItem]
    minimum_random_starting_items: int
    maximum_random_starting_items: int

    def __post_init__(self):
        item_database = default_database.item_database_for_game(self.game)

        _check_matching_items(self.items_state.keys(), item_database.major_items.values())
        _check_matching_items(self.default_items.keys(), item_database.default_items.keys())

        for item, state in self.items_state.items():
            state.check_consistency(item)

        for category, options in item_database.default_items.items():
            if category not in self.default_items:
                raise ValueError(f"Category {category} is missing an item.")

            if self.default_items[category] not in options:
                raise ValueError(f"Category {category} has {self.default_items[category]} as default item, "
                                 f"but that's not a valid option.")

    @property
    def as_json(self) -> dict:
        return {
            "items_state": {
                major_item.name: state.as_json
                for major_item, state in self.items_state.items()
            },
            "default_items": {
                category.name: item.name
                for category, item in self.default_items.items()
            },
            "minimum_random_starting_items": self.minimum_random_starting_items,
            "maximum_random_starting_items": self.maximum_random_starting_items,
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> "MajorItemsConfiguration":
        item_database = default_database.item_database_for_game(game)

        items_state = {}
        for name, item in item_database.major_items.items():
            if name in value["items_state"]:
                state = MajorItemState.from_json(value["items_state"][name])
            else:
                state = MajorItemState()
            items_state[item] = state

        default_items = {
            category: item_database.major_items[value["default_items"][category.name]]
            for category, _ in item_database.default_items.items()
        }

        return cls(
            game=game,
            items_state=items_state,
            default_items=default_items,
            minimum_random_starting_items=value["minimum_random_starting_items"],
            maximum_random_starting_items=value["maximum_random_starting_items"],
        )

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        reference: MajorItemsConfiguration = metadata["reference"]

        name_to_item: Dict[str, MajorItem] = {item.name: item for item in self.items_state.keys()}

        modified_items = sorted(
            item.name for item, state in self.items_state.items()
            if state != reference.items_state[item]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_items, sorted(name_to_item.keys()))
        for item_name in modified_items:
            item = name_to_item[item_name]
            yield from self.items_state[item].bit_pack_encode(item, reference=reference.items_state[item])

        # default_items
        for category, default in self.default_items.items():
            all_major = [major for major in reference.items_state.keys() if major.item_category == category]
            yield from bitpacking.pack_array_element(default, all_major)

        # random starting items
        yield from bitpacking.encode_big_int(self.minimum_random_starting_items)
        yield from bitpacking.encode_big_int(self.maximum_random_starting_items)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "MajorItemsConfiguration":
        reference: MajorItemsConfiguration = metadata["reference"]

        name_to_item: Dict[str, MajorItem] = {item.name: item for item in reference.items_state.keys()}
        modified_items = bitpacking.decode_sorted_array_elements(decoder, sorted(name_to_item.keys()))

        items_state = copy.copy(reference.items_state)
        for item_name in modified_items:
            item = name_to_item[item_name]
            items_state[item] = MajorItemState.bit_pack_unpack(decoder, item,
                                                               reference=reference.items_state[item])

        # default_items
        default_items = {}
        for category in reference.default_items.keys():
            all_major = [major for major in reference.items_state.keys() if major.item_category == category]
            default_items[category] = decoder.decode_element(all_major)

        # random starting items
        minimum = bitpacking.decode_big_int(decoder)
        maximum = bitpacking.decode_big_int(decoder)

        return cls(
            game=reference.game,
            items_state=items_state,
            default_items=default_items,
            minimum_random_starting_items=minimum,
            maximum_random_starting_items=maximum,
        )

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

    def replace_default_item(self, category: ItemCategory, item: MajorItem) -> "MajorItemsConfiguration":
        """
        Creates a copy of this MajorItemsConfiguration where the default item for the given category
        is replaced by the given item.
        :param category:
        :param item:
        :return:
        """
        default_items = copy.copy(self.default_items)
        default_items[category] = item
        return dataclasses.replace(self, default_items=default_items)

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
