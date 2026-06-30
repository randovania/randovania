from __future__ import annotations

from typing import override

from randovania.games.prime2.generator.hint_distributor import BaseEchoesHintDistributor


class EchoesOPRHintDistributor(BaseEchoesHintDistributor):
    @override
    @property
    def num_joke_hints(self) -> int:
        # TODO: rebalance according to the hints that were pulled out of the pool
        return 9
