from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    Hint,
    HintItemPrecision,
    HintLocationPrecision,
    HintType,
    PrecisionPair,
)
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.hint_distributor import HintProvider


# TODO: add tests for distributor after hint system is confirmed
class FusionHintDistributor(HintDistributor):
    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        return [
            PrecisionPair(HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, True),
        ]

    def _get_relative_hint_providers(self) -> list[HintProvider]:
        return []

    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        hints_to_replace: dict[NodeIdentifier, Hint] = {
            identifier: hint
            for identifier, hint in patches.hints.items()
            if hint.precision is None and hint.hint_type == HintType.LOCATION
        }

        for node, hint in hints_to_replace.items():
            db_node = player_pool.game.region_list.node_by_identifier(node)
            hints_to_replace[node] = dataclasses.replace(
                hints_to_replace[node],
                precision=PrecisionPair(
                    HintLocationPrecision[db_node.extra["location_precision"]],
                    HintItemPrecision[db_node.extra["item_precision"]],
                    include_owner=True,
                    relative=None,
                ),
            )

        # Replace the hints the in the patches
        return dataclasses.replace(
            patches,
            hints={identifier: hints_to_replace.get(identifier, hint) for identifier, hint in patches.hints.items()},
        )
        return self.add_hints_precision(player_state, patches, rng)
