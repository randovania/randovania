from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING, TypeVar

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackDecoder, BitPackValue
from randovania.game_description import default_database
from randovania.layout.base.standard_pickup_state import StandardPickupState

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.pickup.pickup_category import PickupCategory
    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
    from randovania.games.game import RandovaniaGame

T = TypeVar("T")


def _check_matching_pickups(actual: Iterable[T], reference: Iterable[T]):
    actual_pickups = set(actual)
    reference_pickups = set(reference)
    if actual_pickups != reference_pickups:
        raise ValueError(f"Non-matching keys: Has {actual_pickups}, expected {reference_pickups}.")


@dataclasses.dataclass(frozen=True)
class StandardPickupConfiguration(BitPackValue):
    game: RandovaniaGame
    pickups_state: dict[StandardPickupDefinition, StandardPickupState]
    default_pickups: dict[PickupCategory, StandardPickupDefinition]
    minimum_random_starting_pickups: int
    maximum_random_starting_pickups: int

    def __post_init__(self):
        pickup_database = default_database.pickup_database_for_game(self.game)

        _check_matching_pickups(self.pickups_state.keys(), pickup_database.standard_pickups.values())
        _check_matching_pickups(self.default_pickups.keys(), pickup_database.default_pickups.keys())

        for item, state in self.pickups_state.items():
            state.check_consistency(item)

        for category, options in pickup_database.default_pickups.items():
            if category not in self.default_pickups:
                raise ValueError(f"Category {category} is missing an item.")

            if self.default_pickups[category] not in options:
                raise ValueError(
                    f"Category {category} has {self.default_pickups[category]} as default item, "
                    f"but that's not a valid option."
                )

    @property
    def as_json(self) -> dict:
        return {
            "pickups_state": {pickup.name: state.as_json for pickup, state in self.pickups_state.items()},
            "default_pickups": {category.name: pickup.name for category, pickup in self.default_pickups.items()},
            "minimum_random_starting_pickups": self.minimum_random_starting_pickups,
            "maximum_random_starting_pickups": self.maximum_random_starting_pickups,
        }

    @classmethod
    def from_json(cls, value: dict, game: RandovaniaGame) -> StandardPickupConfiguration:
        pickup_database = default_database.pickup_database_for_game(game)

        pickups_state = {}
        for name, pickup in pickup_database.standard_pickups.items():
            if name in value["pickups_state"]:
                state = StandardPickupState.from_json(value["pickups_state"][name])
            else:
                state = StandardPickupState()
            pickups_state[pickup] = state

        default_pickups = {
            category: pickup_database.standard_pickups[value["default_pickups"][category.name]]
            for category, _ in pickup_database.default_pickups.items()
        }

        return cls(
            game=game,
            pickups_state=pickups_state,
            default_pickups=default_pickups,
            minimum_random_starting_pickups=value["minimum_random_starting_pickups"],
            maximum_random_starting_pickups=value["maximum_random_starting_pickups"],
        )

    def bit_pack_encode(self, metadata) -> Iterator[tuple[int, int]]:
        reference: StandardPickupConfiguration = metadata["reference"]

        name_to_pickup: dict[str, StandardPickupDefinition] = {
            pickup.name: pickup for pickup in self.pickups_state.keys()
        }

        modified_pickups = sorted(
            pickup.name for pickup, state in self.pickups_state.items() if state != reference.pickups_state[pickup]
        )
        yield from bitpacking.pack_sorted_array_elements(modified_pickups, sorted(name_to_pickup.keys()))
        for pickup_name in modified_pickups:
            pickup = name_to_pickup[pickup_name]
            yield from self.pickups_state[pickup].bit_pack_encode(pickup, reference=reference.pickups_state[pickup])

        # default_items
        for category, default in self.default_pickups.items():
            all_standard = [pickup for pickup in reference.pickups_state.keys() if pickup.pickup_category == category]
            yield from bitpacking.pack_array_element(default, all_standard)

        # random starting items
        yield from bitpacking.encode_big_int(self.minimum_random_starting_pickups)
        yield from bitpacking.encode_big_int(self.maximum_random_starting_pickups)

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> StandardPickupConfiguration:
        reference: StandardPickupConfiguration = metadata["reference"]

        name_to_pickup: dict[str, StandardPickupDefinition] = {
            pickup.name: pickup for pickup in reference.pickups_state.keys()
        }
        modified_pickups = bitpacking.decode_sorted_array_elements(decoder, sorted(name_to_pickup.keys()))

        pickups_state = copy.copy(reference.pickups_state)
        for pickup_name in modified_pickups:
            pickup = name_to_pickup[pickup_name]
            pickups_state[pickup] = StandardPickupState.bit_pack_unpack(
                decoder, pickup, reference=reference.pickups_state[pickup]
            )

        # default_pickups
        default_pickups = {}
        for category in reference.default_pickups.keys():
            all_standard = [pickup for pickup in reference.pickups_state.keys() if pickup.pickup_category == category]
            default_pickups[category] = decoder.decode_element(all_standard)

        # random starting items
        minimum = bitpacking.decode_big_int(decoder)
        maximum = bitpacking.decode_big_int(decoder)

        return cls(
            game=reference.game,
            pickups_state=pickups_state,
            default_pickups=default_pickups,
            minimum_random_starting_pickups=minimum,
            maximum_random_starting_pickups=maximum,
        )

    def get_pickup_with_name(self, name: str) -> StandardPickupDefinition:
        for pickup in self.pickups_state.keys():
            if pickup.name == name:
                return pickup
        raise KeyError(name)

    def replace_state_for_pickup(
        self,
        pickup: StandardPickupDefinition,
        state: StandardPickupState,
    ) -> StandardPickupConfiguration:
        return self.replace_states({pickup: state})

    def replace_states(
        self,
        new_states: dict[StandardPickupDefinition, StandardPickupState],
    ) -> StandardPickupConfiguration:
        """
        Creates a copy of this MajorItemsConfiguration where the state of all given pickups are replaced by the given
        states.
        :param new_states:
        :return:
        """
        pickups_state = copy.copy(self.pickups_state)

        for pickup, state in new_states.items():
            pickups_state[pickup] = state

        return dataclasses.replace(self, pickups_state=pickups_state)

    def replace_default_pickup(
        self,
        category: PickupCategory,
        pickup: StandardPickupDefinition,
    ) -> StandardPickupConfiguration:
        """
        Creates a copy of this MajorItemsConfiguration where the default pickup for the given category
        is replaced by the given pickup.
        :param category:
        :param pickup:
        :return:
        """
        default_pickups = copy.copy(self.default_pickups)
        default_pickups[category] = pickup
        return dataclasses.replace(self, default_pickups=default_pickups)

    def calculate_provided_ammo(self) -> dict[str, int]:
        result: dict[str, int] = {}

        for pickup, state in self.pickups_state.items():
            total_pickups = state.num_shuffled_pickups + state.num_included_in_starting_pickups
            if state.include_copy_in_original_location:
                total_pickups += 1

            for ammo_name, ammo_count in zip(pickup.ammo, state.included_ammo):
                result[ammo_name] = result.get(ammo_name, 0) + ammo_count * total_pickups

        return result

    def dangerous_settings(self) -> list[str]:
        return []  # TODO: remove this if it won't be used?
