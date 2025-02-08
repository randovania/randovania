from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.hint_node import HintNodeKind
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    HintDarkTemple,
    HintItemPrecision,
    PrecisionPair,
    RedTempleHint,
    SpecificHintPrecision,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.generator.hint_distributor import HintDistributor, HintTargetPrecision
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from collections.abc import Container
    from random import Random

    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.generator.filler.filler_configuration import PlayerPool
    from randovania.generator.pre_fill_params import PreFillParams


class EchoesHintDistributor(HintDistributor):
    # Pre Filler
    @override
    @property
    def num_joke_hints(self) -> int:
        return 2

    @override
    def is_pickup_interesting(self, pickup: PickupEntry) -> bool:
        return not pickup.has_hint_feature("key")

    @override
    async def get_guaranteed_hints(self, patches: GamePatches, prefill: PreFillParams) -> list[HintTargetPrecision]:
        def g(index: int, loc: str):
            return (
                PickupIndex(index),
                PrecisionPair(patches.game.hint_feature_database[loc], HintItemPrecision.DETAILED, include_owner=False),
            )

        return [
            g(24, "specific_hint_2mos"),  # Light Suit
            g(43, "specific_hint_guardian"),  # Dark Suit (Amorbis)
            g(79, "specific_hint_guardian"),  # Dark Visor (Chykka)
            g(115, "specific_hint_guardian"),  # Annihilator Beam (Quadraxis)
        ]

    @override
    async def assign_other_hints(
        self, patches: GamePatches, identifiers: list[NodeIdentifier], prefill: PreFillParams
    ) -> GamePatches:
        all_hint_identifiers = [identifier for identifier in identifiers if identifier not in patches.hints]
        prefill.rng.shuffle(all_hint_identifiers)

        # Dark Temple hints
        temple_hints = list(enum_lib.iterate_enum(HintDarkTemple))
        while all_hint_identifiers and temple_hints:
            identifier = all_hint_identifiers.pop()
            patches = patches.assign_hint(identifier, RedTempleHint(dark_temple=temple_hints.pop(0)))
            identifiers.remove(identifier)

        return patches

    # Post Filler
    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    async def assign_precision_to_hints(
        self,
        patches: GamePatches,
        rng: Random,
        player_pool: PlayerPool,
        player_pools: list[PlayerPool],
        hint_kinds: Container[HintNodeKind] = {HintNodeKind.GENERIC},
    ) -> GamePatches:
        assert isinstance(player_pool.configuration, EchoesConfiguration)
        if player_pool.configuration.hints.item_hints:
            return await super().assign_precision_to_hints(patches, rng, player_pool, player_pools, hint_kinds)
        else:
            return self.replace_hints_without_precision_with_jokes(patches)

    @override
    async def get_specific_pickup_precision_pairs(self) -> dict[NodeIdentifier, PrecisionPair]:
        game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)
        keybearer = game.hint_feature_database["specific_hint_keybearer"]

        precision = PrecisionPair(keybearer, SpecificHintPrecision(0.4), include_owner=True)

        c = NodeIdentifier.create
        keybearers = [
            c("Agon Wastes", "Central Mining Station", "Keybearer Corpse (J-Stl)"),
            c("Agon Wastes", "Main Reactor", "Keybearer Corpse (B-Stl)"),
            c("Sanctuary Fortress", "Sanctuary Entrance", "Keybearer Corpse (S-Jrs)"),
            c("Sanctuary Fortress", "Dynamo Works", "Keybearer Corpse (C-Rch)"),
            c("Temple Grounds", "Landing Site", "Keybearer Corpse (M-Dhe)"),
            c("Temple Grounds", "Industrial Site", "Keybearer Corpse (J-Fme)"),
            c("Temple Grounds", "Storage Cavern A", "Keybearer Corpse (D-Isl)"),
            c("Torvus Bog", "Torvus Lagoon", "Keybearer Corpse (S-Dly)"),
            c("Torvus Bog", "Catacombs", "Keybearer Corpse (G-Sch)"),
        ]

        return {keybearer: precision for keybearer in keybearers}

    @override
    @property
    def use_region_location_precision(self) -> bool:
        return False
