from dataclasses import dataclass
from typing import Dict, Tuple

from randovania.game_description.dock import DockWeakness
from randovania.game_description.node import TeleporterConnection, DockConnection
from randovania.game_description.resources import PickupAssignment


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
