import copy
from dataclasses import dataclass
from typing import Dict, Tuple, Iterator

from randovania.game_description.dock import DockWeakness
from randovania.game_description.node import TeleporterConnection, DockConnection
from randovania.game_description.resources import PickupAssignment, PickupIndex, PickupEntry


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

    @classmethod
    def empty(cls) -> "GamePatches":
        return GamePatches({}, {}, {}, {})

    def assign_new_pickups(self, assignments: Iterator[Tuple[PickupIndex, PickupEntry]]) -> "GamePatches":
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return GamePatches(
            new_pickup_assignment,
            self.elevator_connection,
            self.dock_connection,
            self.dock_weakness
        )
