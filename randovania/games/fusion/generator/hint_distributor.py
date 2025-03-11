from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    JokeHint,
    PrecisionPair,
)
from randovania.games.fusion.layout.fusion_configuration import FusionConfiguration
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.hint_node import HintNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.pre_fill_params import PreFillParams


class FusionHintDistributor(HintDistributor):
    # Pre Filler
    # Joke hints to go in pool
    @override
    @property
    def num_joke_hints(self) -> int:
        return 0

    # Makes the listed features less interesting to hint
    @override
    def is_pickup_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        non_interesting_features = ["key", "energy_tank", "charge"]
        for feature in non_interesting_features:
            if target.pickup.has_hint_feature(feature):
                return False
        return True

    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        assert isinstance(prefill.configuration, FusionConfiguration)
        fake_hints = [
            {
                "region": "Main Deck",
                "area": "Auxiliary Navigation Room",
                "node": "Navigation Terminal",
                "type": JokeHint(),
            },
            {
                "region": "Main Deck",
                "area": "Restricted Navigation Room",
                "node": "Navigation Terminal",
                "type": JokeHint(),
            },
        ]
        for hint in fake_hints:
            patches = patches.assign_hint(
                NodeIdentifier.create(hint["region"], hint["area"], hint["node"]), hint["type"]
            )

        return await super().assign_specific_location_hints(patches, prefill)

    # Post Filler
