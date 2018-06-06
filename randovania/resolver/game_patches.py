from typing import NamedTuple, List


class GamePatches(NamedTuple):
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    pickup_mapping: List[int]
