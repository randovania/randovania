from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.hint import (
    Hint,
    HintDarkTemple,
    HintItemPrecision,
    HintLocationPrecision,
    HintRelativeAreaName,
    HintType,
    PrecisionPair,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.generator.hint_distributor import HintDistributor, HintTargetPrecision
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.pre_fill_params import PreFillParams


class EchoesHintDistributor(HintDistributor):
    # Pre Filler
    @property
    def num_joke_hints(self) -> int:
        return 2

    async def get_guaranteed_hints(self, patches: GamePatches, prefill: PreFillParams) -> list[HintTargetPrecision]:
        def g(index, loc):
            return (
                PickupIndex(index),
                PrecisionPair(loc, HintItemPrecision.DETAILED, include_owner=False),
            )

        return [
            g(24, HintLocationPrecision.LIGHT_SUIT_LOCATION),  # Light Suit
            g(43, HintLocationPrecision.GUARDIAN),  # Dark Suit (Amorbis)
            g(79, HintLocationPrecision.GUARDIAN),  # Dark Visor (Chykka)
            g(115, HintLocationPrecision.GUARDIAN),  # Annihilator Beam (Quadraxis)
        ]

    async def assign_other_hints(
        self, patches: GamePatches, identifiers: list[NodeIdentifier], prefill: PreFillParams
    ) -> GamePatches:
        all_hint_identifiers = [identifier for identifier in identifiers if identifier not in patches.hints]
        prefill.rng.shuffle(all_hint_identifiers)

        # Dark Temple hints
        temple_hints = list(enum_lib.iterate_enum(HintDarkTemple))
        while all_hint_identifiers and temple_hints:
            identifier = all_hint_identifiers.pop()
            patches = patches.assign_hint(
                identifier, Hint(HintType.RED_TEMPLE_KEY_SET, None, dark_temple=temple_hints.pop(0))
            )
            identifiers.remove(identifier)

        return patches

    # Post Filler

    def precision_pair_weighted_list(self) -> list[PrecisionPair]:
        tiers = {
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, False): 3,
            (HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, True): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.PRECISE_CATEGORY, True): 2,
            (HintLocationPrecision.DETAILED, HintItemPrecision.GENERAL_CATEGORY, True): 1,
            (HintLocationPrecision.REGION_ONLY, HintItemPrecision.DETAILED, False): 2,
            (HintLocationPrecision.REGION_ONLY, HintItemPrecision.PRECISE_CATEGORY, True): 1,
        }

        hints = []
        for params, quantity in tiers.items():
            hints.extend([PrecisionPair(*params)] * quantity)

        return hints

    def _get_relative_hint_providers(self):
        return [
            self._relative(HintLocationPrecision.RELATIVE_TO_AREA, True, HintRelativeAreaName.NAME, 4),
            self._relative(HintLocationPrecision.RELATIVE_TO_AREA, False, HintRelativeAreaName.NAME, 3),
            self._relative(HintLocationPrecision.RELATIVE_TO_INDEX, True, HintItemPrecision.DETAILED, 4),
        ]

    async def assign_precision_to_hints(
        self, patches: GamePatches, rng: Random, player_pool: PlayerPool, player_state: PlayerState
    ) -> GamePatches:
        assert isinstance(player_pool.configuration, EchoesConfiguration)
        if player_pool.configuration.hints.item_hints:
            return self.add_hints_precision(player_state, patches, rng)
        else:
            return self.replace_hints_without_precision_with_jokes(patches)
