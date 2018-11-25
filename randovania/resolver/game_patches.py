from typing import NamedTuple

from randovania.game_description.resources import PickupAssignment


class GamePatches(NamedTuple):
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    pickup_assignment: PickupAssignment
