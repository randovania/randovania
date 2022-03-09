from __future__ import annotations

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler.player_state import PlayerState

WeightedLocations = dict[tuple[PlayerState, PickupIndex], float]
