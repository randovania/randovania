from __future__ import annotations

from typing import override

from randovania.game_description.hint import PrecisionPair
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
