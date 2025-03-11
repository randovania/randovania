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
        return 1

    # Makes the listed features less interesting to hint
    @override
    def is_pickup_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        non_interesting_features = ["key", "charge"]
        for feature in non_interesting_features:
            if target.pickup.has_hint_feature(feature):
                return False
        return True

    # Set default precision for hints
    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    # Make hints for specific locations
    @override
    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        assert isinstance(prefill.configuration, FusionConfiguration)
        fake_hints = [
            ("Main Deck", "Auxiliary Navigation Room", "Navigation Terminal"),
            ("Main Deck", "Restricted Navigation Room", "Navigation Terminal"),
        ]
        for region, area, node in fake_hints:
            patches = patches.assign_hint(NodeIdentifier.create(region, area, node), JokeHint())

        return await super().assign_specific_location_hints(patches, prefill)

    # Post Filler

    # Don't use area in hints
    @override
    @property
    def use_detailed_location_precision(self) -> bool:
        return False
