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
    _items: list[tuple[PlayerState, dict[PickupIndex, float]]]

    def __init__(self, items: list[tuple[PlayerState, dict[PickupIndex, float]]]):
        self._items = items

    def __hash__(self) -> int:
        return hash(self._items)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, WeightedLocations) and self._items == other._items

    def __str__(self) -> str:
        return str(self._items)

    def __repr__(self) -> str:
        return f"WeightedLocations({self._items!r})"

    def is_empty(self) -> bool:
        """True if there are no locations."""
        return all(not locations for _, locations in self._items)

    def total_count(self) -> int:
        """How many locations are available, across all worlds."""
        return sum(len(locations) for _, locations in self._items)

    def _locations_for_player(self, player: PlayerState) -> dict[PickupIndex, float]:
        for p, locations in self._items:
            if p == player:
                return locations
        raise KeyError(f"Unknown player: {player}")

    def count_for_player(self, player: PlayerState) -> int:
        """How many locations are available, for one player in particular."""
        return len(self._locations_for_player(player))

    def filter_for_player(self, player: PlayerState) -> WeightedLocations:
        """Returns only the locations of one player in particular."""
        return WeightedLocations([entry if entry[0] == player else (entry[0], {}) for entry in self._items])

    def filter_major_minor_for_pickup(self, pickup: PickupEntry) -> WeightedLocations:
        """Returns only the locations whose player's major/minor configuration allow this pickup."""
        return WeightedLocations(
            [
                (
                    player,
                    {index: weight for index, weight in locations.items() if player.can_place_pickup_at(pickup, index)},
                )
                for player, locations in self._items
            ]
        )

    def all_items(self) -> Iterator[tuple[PlayerState, PickupIndex, float]]:
        for player, locations in self._items:
            for index, weight in locations.items():
                yield player, index, weight

    def select_location(self, rng: Random) -> tuple[PlayerState, PickupIndex]:
        return random_lib.select_element_with_weight(
            rng, {(player, index): weight for player, locations in self._items for index, weight in locations.items()}
        )

    def remove(self, player: PlayerState, index: PickupIndex) -> None:
        self._locations_for_player(player).pop(index)

    def can_fit(self, action: Action, *, extra_indices: int = 0) -> bool:
        # Find how many locations are major, minor or both
        num_major_locs = 0
        num_minor_locs = 0
        num_free_locs = extra_indices

        for player, locations in self._items:
            if player.configuration.randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
                for index in locations.keys():
                    if player.get_location_category(index) == LocationCategory.MAJOR:
                        num_major_locs += 1
                    else:
                        num_minor_locs += 1
            else:
                num_free_locs += len(locations)

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
