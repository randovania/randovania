from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    HintItemPrecision,
    HintLocationPrecision,
    JokeHint,
    PrecisionPair,
)
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.generator.pre_fill_params import PreFillParams


class DreadHintDistributor(HintDistributor):
    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair(HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, True)

    @override
    def is_pickup_interesting(self, pickup: PickupEntry) -> bool:
        return not pickup.has_hint_feature("dna")

    @override
    async def assign_specific_location_hints(self, patches: GamePatches, prefill: PreFillParams) -> GamePatches:
        assert isinstance(prefill.configuration, DreadConfiguration)
        if prefill.configuration.artifacts.required_artifacts > 0:
            patches = patches.assign_hint(
                NodeIdentifier.create("Dairon", "Navigation Station North", "Save Station"), JokeHint()
            )

        return await super().assign_specific_location_hints(patches, prefill)
