import copy
from dataclasses import dataclass
from typing import Dict, Tuple, Iterator, Optional

from randovania.game_description.dock import DockWeakness
from randovania.game_description.node import TeleporterConnection, DockConnection
from randovania.game_description.resources import PickupAssignment, PickupIndex, PickupEntry, SimpleResourceInfo
from randovania.game_description.area_location import AreaLocation


@dataclass(frozen=True)
class GamePatches:
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    pickup_assignment: PickupAssignment
    elevator_connection: Dict[int, TeleporterConnection]
    dock_connection: Dict[Tuple[int, int], DockConnection]
    dock_weakness: Dict[Tuple[int, int], DockWeakness]
    custom_initial_items: Optional[Dict[SimpleResourceInfo, int]]
    starting_location: AreaLocation

    @classmethod
    def with_game(cls, game: "GameDescription") -> "GamePatches":
        return GamePatches({}, {}, {}, {}, None, game.starting_location)

    def assign_new_pickups(self, assignments: Iterator[Tuple[PickupIndex, PickupEntry]]) -> "GamePatches":
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return GamePatches(
            new_pickup_assignment,
            self.elevator_connection,
            self.dock_connection,
            self.dock_weakness,
            self.custom_initial_items,
            self.starting_location,
        )

    def assign_pickup_assignment(self, assignment: PickupAssignment) -> "GamePatches":
        items: Iterator[Tuple[PickupIndex, PickupEntry]] = assignment.items()
        return self.assign_new_pickups(items)
