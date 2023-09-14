from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.resources.location_category import LocationCategory
from randovania.layout.base.available_locations import RandomizationMode
from randovania.lib import random_lib

if TYPE_CHECKING:
    from collections.abc import Iterator
    from random import Random

    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.generator.filler.action import Action
    from randovania.generator.filler.player_state import PlayerState


class WeightedLocations:
    _items: dict[tuple[PlayerState, PickupIndex], float]

    def __init__(self, items: dict[tuple[PlayerState, PickupIndex], float]):
        self._items = items

    def __eq__(self, other: object) -> bool:
        return isinstance(other, WeightedLocations) and self._items == other._items

    def __str__(self) -> str:
        return str(self._items)

    def is_empty(self) -> bool:
        """True if there are no locations."""
        return not self._items

    def total_count(self) -> int:
        """How many locations are available, across all worlds."""
        return len(self._items)

    def count_for_player(self, player: PlayerState) -> int:
        """How many locations are available, for one player in particular."""
        return sum(1 for p, _ in self._items.keys() if p == player)

    def filter_for_player(self, player: PlayerState) -> WeightedLocations:
        """Returns only the locations of one player in particular."""
        return WeightedLocations({loc: weight for loc, weight in self._items.items() if loc[0] is player})

    def filter_major_minor_for_pickup(self, pickup: PickupEntry) -> WeightedLocations:
        """Returns only the locations whose player's major/minor configuration allow this pickup."""
        return WeightedLocations(
            {
                (player, index): weight
                for (player, index), weight in self._items.items()
                if player.can_place_pickup_at(pickup, index)
            }
        )

    def all_items(self) -> Iterator[tuple[PlayerState, PickupIndex, float]]:
        for (player, index), weight in self._items.items():
            yield player, index, weight

    def select_location(self, rng: Random) -> tuple[PlayerState, PickupIndex]:
        return random_lib.select_element_with_weight(self._items, rng)

    def remove(self, player: PlayerState, index: PickupIndex) -> None:
        self._items.pop((player, index))

    def can_fit(self, action: Action, *, extra_indices: int = 0) -> bool:
        # Find how many locations are major, minor or both
        num_major_locs = 0
        num_minor_locs = 0
        num_free_locs = extra_indices
        for player, index in self._items.keys():
            if player.configuration.randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
                if player.get_location_category(index) == LocationCategory.MAJOR:
                    num_major_locs += 1
                else:
                    num_minor_locs += 1
            else:
                num_free_locs += 1

        # Count how many pickups are major and minor in the action
        num_major_picks = 0
        num_minor_picks = 0
        for pickup in action.split_pickups()[1]:
            if pickup.generator_params.preferred_location_category == LocationCategory.MAJOR:
                num_major_picks += 1
            else:
                num_minor_picks += 1

        # Calculate the answer
        num_major_picks = max(0, num_major_picks - num_major_locs)
        num_minor_picks = max(0, num_minor_picks - num_minor_locs)
        num_remaining_picks = num_major_picks + num_minor_picks
        return num_remaining_picks <= num_free_locs
