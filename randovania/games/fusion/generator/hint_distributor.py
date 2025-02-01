from __future__ import annotations

from randovania.game_description.hint import (
    HintItemPrecision,
    HintLocationPrecision,
    PrecisionPair,
)
from randovania.generator.hint_distributor import HintDistributor


# TODO: add tests for distributor after hint system is confirmed
class FusionHintDistributor(HintDistributor):
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair(HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, True)
