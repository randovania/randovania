from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision, PrecisionPair
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.filler.player_state import PlayerState


class PrimeHintDistributor(HintDistributor):
    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        return [
            PrecisionPair(HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, True),
        ]

    def _get_relative_hint_providers(self):
        return []

    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        return self.add_hints_precision(player_state, patches, rng)
