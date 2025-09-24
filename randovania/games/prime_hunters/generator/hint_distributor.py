from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import JokeHint, PrecisionPair
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.hint_node import HintNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.pre_fill_params import PreFillParams


class HuntersHintDistributor(HintDistributor):
    @override
    @property
    def num_joke_hints(self) -> int:
        return 0

    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    def is_pickup_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        return not target.pickup.has_hint_feature("octolith")

    @override
    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        assert isinstance(prefill.configuration, HuntersConfiguration)
        fake_hints = [
            ("Alinos", "Alimbic Cannon Control Room", "Lore Scan 1"),
            ("Alinos", "Alimbic Cannon Control Room", "Lore Scan 2"),
            ("Alinos", "Alimbic Cannon Control Room", "Lore Scan 3"),
            ("Alinos", "Alimbic Cannon Control Room", "Lore Scan 4"),
        ]
        for region, area, node in fake_hints:
            patches = patches.assign_hint(NodeIdentifier.create(region, area, node), JokeHint())

        return await super().assign_specific_location_hints(patches, prefill)
