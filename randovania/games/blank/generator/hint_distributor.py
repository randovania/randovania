from __future__ import annotations

from typing import override

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision, PrecisionPair
from randovania.generator.hint_distributor import HintDistributor


class BlankHintDistributor(HintDistributor):
    @override
    @property
    def num_joke_hints(self) -> int:
        return 0

    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    async def get_specific_location_precision_pairs(self) -> dict[NodeIdentifier, PrecisionPair]:
        c = NodeIdentifier.create
        precision = PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED)

        return {
            c("Intro", "Hint Room", "Hint specific Location"): precision,
        }
