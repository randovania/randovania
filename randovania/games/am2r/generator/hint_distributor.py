from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_entry import PickupEntry


class AM2RHintDistributor(HintDistributor):
    # Makes DNA less likely to be hinted since gaurunteed hints already exist on Wisdom Septoggs
    @override
    def is_pickup_interesting(self, pickup: PickupEntry) -> bool:
        return not pickup.has_hint_feature("dna")
