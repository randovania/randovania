from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.hint import PrecisionPair
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.hint_node import HintNode


class MSRHintDistributor(HintDistributor):
    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    def is_pickup_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        non_interesting_features = ["dna", "energy_tank", "expansion", "reserve_tank"]
        for feature in non_interesting_features:
            if target.pickup.has_hint_feature(feature):
                return False
        return True

    @property
    def use_detailed_location_precision(self) -> bool:
        return False
