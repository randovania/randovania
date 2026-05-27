from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    PrecisionPair,
    SpecificHintPrecision,
)
from randovania.generator.hint_distributor import HintDistributor

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.hint_node import HintNode


class EchoesHintDistributor(HintDistributor):
    # Pre Filler
    @override
    @property
    def num_joke_hints(self) -> int:
        return 9

    @override
    def is_pickup_more_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        interesting_features = ["cheat", "energy_tank"]
        for feature in interesting_features:
            if target.pickup.has_hint_feature(feature):
                return False
        return super().is_pickup_more_interesting(target, player_id, hint_node)

    @override
    def is_pickup_interesting(self, target: PickupTarget, player_id: int, hint_node: HintNode) -> bool:
        non_interesting_features = ["key"]
        for feature in non_interesting_features:
            if target.pickup.has_hint_feature(feature):
                return False
        if target.player == player_id and ("Translator" in target.pickup.name):
            # don't place a translator hint on its color of lore scan
            return hint_node.extra["translator"] not in target.pickup.name
        return super().is_pickup_interesting(target, player_id, hint_node)

    # Post Filler
    @override
    @property
    def default_precision_pair(self) -> PrecisionPair:
        return PrecisionPair.featural()

    @override
    async def get_specific_location_precision_pairs(self) -> dict[NodeIdentifier, PrecisionPair]:
        game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)
        keybearer = game.hint_feature_database["specific_hint_keybearer"]

        precision = PrecisionPair(keybearer, SpecificHintPrecision(0.65, 0.1), include_owner=True)

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

        return dict.fromkeys(keybearers, precision)

    @override
    @property
    def use_region_location_precision(self) -> bool:
        return False
