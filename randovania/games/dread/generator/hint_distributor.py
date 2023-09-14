from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import Hint, HintItemPrecision, HintLocationPrecision, HintType, PrecisionPair
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.pre_fill_params import PreFillParams


class DreadHintDistributor(HintDistributor):
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

    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        assert isinstance(prefill.configuration, DreadConfiguration)
        if prefill.configuration.artifacts.required_artifacts > 0:
            patches = patches.assign_hint(
                NodeIdentifier.create("Dairon", "Navigation Station North", "Save Station"), Hint(HintType.JOKE, None)
            )

        return await super().assign_specific_location_hints(patches, prefill)
