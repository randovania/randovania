from typing import NamedTuple, List, Optional


class GamePatches(NamedTuple):
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    item_loss_enabled: bool
    pickup_mapping: List[Optional[int]]
