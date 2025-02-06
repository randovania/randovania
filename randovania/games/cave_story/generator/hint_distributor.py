from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNodeKind
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision, LocationHint, PrecisionPair
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.generator.hint_distributor import HintDistributor, HintTargetPrecision

if TYPE_CHECKING:
    from collections.abc import Container
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.hint_distributor import HintFeatureGaussianParams
    from randovania.generator.pre_fill_params import PreFillParams

USE_GUARANTEED_HINTS = False


class CSHintDistributor(HintDistributor):
    @override
    @property
    def num_joke_hints(self) -> int:
        return 0

    @override
    async def get_specific_pickup_precision_pairs(self) -> dict[NodeIdentifier, PrecisionPair]:
        game = default_database.game_description_for(RandovaniaGame.CAVE_STORY)

        def p(loc: str) -> PrecisionPair:
            return PrecisionPair(game.hint_feature_database[loc], HintItemPrecision.DETAILED, False)

        c = NodeIdentifier.create

        return {
            c("Grasstown", "Power Room", "Hint - MALCO"): p("specific_hint_malco"),
            c("Ruined Egg Corridor", "Little House", "Hint - Mrs. Little"): p("specific_hint_little"),
            c("Sand Zone", "Jenka's House", "Hint - Jenka 1"): p("specific_hint_jenka"),
            c("Sand Zone", "Jenka's House", "Hint - Jenka 2"): p("specific_hint_jenka"),
            c("Plantation", "Statue Chamber", "Hint - Numahachi 1"): p("specific_hint_numahachi"),
            c("Plantation", "Statue Chamber", "Hint - Numahachi 2"): p("specific_hint_numahachi"),
        }

    @override
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

            already_hinted_indices = [hint.target for hint in patches.hints.values() if isinstance(hint, LocationHint)]
            indices_with_hint = [
                (node.pickup_index, PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, False))
                for node in patches.game.region_list.iterate_nodes()
                if isinstance(node, PickupNode)
                and node.pickup_index not in already_hinted_indices
                and patches.pickup_assignment[node.pickup_index].pickup.name in items_with_hint
            ]
            return indices_with_hint

        return []

    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    @property
    def use_region_location_precision(self) -> bool:
        return False

    @override
    async def assign_precision_to_hints(
        self,
        patches: GamePatches,
        rng: Random,
        player_pool: PlayerPool,
        player_pools: list[PlayerPool],
        hint_kinds: Container[HintNodeKind] = {HintNodeKind.GENERIC},
    ) -> GamePatches:
        assert isinstance(player_pool.configuration, CSConfiguration)
        if player_pool.configuration.hints.item_hints:
            return await super().assign_precision_to_hints(patches, rng, player_pool, player_pools, hint_kinds)
        else:
            return self.replace_hints_without_precision_with_jokes(patches)

    @override
    @classmethod
    def location_feature_distribution(cls) -> HintFeatureGaussianParams:
        return 0.75, 0.07
