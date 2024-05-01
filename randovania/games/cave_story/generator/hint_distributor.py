from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision, PrecisionPair
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.generator.hint_distributor import HintDistributor, HintTargetPrecision

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.pre_fill_params import PreFillParams

USE_GUARANTEED_HINTS = False


class CSHintDistributor(HintDistributor):
    @property
    def num_joke_hints(self) -> int:
        return 0

    async def get_specific_pickup_precision_pair_overrides(
        self, patches: GamePatches, prefill: PreFillParams
    ) -> dict[NodeIdentifier, PrecisionPair]:
        def p(loc):
            return PrecisionPair(loc, HintItemPrecision.DETAILED, False)

        c = NodeIdentifier.create

        return {
            c("Grasstown", "Power Room", "Hint - MALCO"): p(HintLocationPrecision.MALCO),
            c("Ruined Egg Corridor", "Little House", "Hint - Mrs. Little"): p(HintLocationPrecision.LITTLE),
            c("Sand Zone", "Jenka's House", "Hint - Jenka 1"): p(HintLocationPrecision.JENKA),
            c("Sand Zone", "Jenka's House", "Hint - Jenka 2"): p(HintLocationPrecision.JENKA),
            c("Plantation", "Statue Chamber", "Hint - Numahachi 1"): p(HintLocationPrecision.NUMAHACHI),
            c("Plantation", "Statue Chamber", "Hint - Numahachi 2"): p(HintLocationPrecision.NUMAHACHI),
        }

    async def get_guaranteed_hints(self, patches: GamePatches, prefill: PreFillParams) -> list[HintTargetPrecision]:
        if USE_GUARANTEED_HINTS:
            assert isinstance(patches.configuration, CSConfiguration)
            # TODO: assign base hints *after* generation?
            items_with_hint = []
            if patches.configuration.objective == CSObjective.BAD_ENDING:
                items_with_hint.append("Rusty Key")
            else:
                items_with_hint.append("ID Card")
            if patches.starting_location.area != "Start Point":
                items_with_hint.append("Arthur's Key")

            already_hinted_indices = [hint.target for hint in patches.hints.values() if hint.target is not None]
            indices_with_hint = [
                (node.pickup_index, HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED)
                for node in patches.game.region_list.iterate_nodes()
                if isinstance(node, PickupNode)
                and node.pickup_index not in already_hinted_indices
                and patches.pickup_assignment[node.pickup_index].pickup.name in items_with_hint
            ]
            return indices_with_hint

        return []

    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        tiers = {
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, True): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.PRECISE_CATEGORY, True): 1,
            (HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, True): 1,
        }

        hints = []
        for params, quantity in tiers.items():
            hints.extend([PrecisionPair(*params)] * quantity)

        return hints

    def _get_relative_hint_providers(self):
        return []

    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        assert isinstance(player_pool.configuration, CSConfiguration)
        if player_pool.configuration.hints.item_hints:
            return self.add_hints_precision(player_state, patches, rng)
        else:
            return self.replace_hints_without_precision_with_jokes(patches)
