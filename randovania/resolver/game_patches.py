from typing import NamedTuple, Dict

from randovania.game_description.resources import PickupIndex, PickupEntry

PickupAssignment = Dict[PickupIndex, PickupEntry]


class GamePatches(NamedTuple):
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    pickup_assignment: PickupAssignment
