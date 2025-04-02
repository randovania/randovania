from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.resources.pickup_index import PickupIndex

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.pickup.pickup_entry import PickupEntry


@dataclasses.dataclass(frozen=True)
class PoolResults:
    to_place: list[PickupEntry]
    assignment: dict[PickupIndex, PickupEntry]
    starting: list[PickupEntry]

    def __post_init__(self) -> None:
        for key in self.assignment:
            if not isinstance(key, PickupIndex):
                raise TypeError(f"{key} is not a PickupIndex")

    def extend_with(self, extension: PoolResults) -> None:
        self.to_place.extend(extension.to_place)
        self.assignment.update(extension.assignment)
        self.starting.extend(extension.starting)

    def pickups_in_world(self) -> Iterator[PickupEntry]:
        """Pickups that are or will end up placed in a world."""
        yield from self.to_place
        yield from self.assignment.values()

    def all_pickups(self) -> Iterator[PickupEntry]:
        yield from self.pickups_in_world()
        yield from self.starting
