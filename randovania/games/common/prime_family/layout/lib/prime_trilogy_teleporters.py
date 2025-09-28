from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode


@dataclasses.dataclass(frozen=True)
class PrimeTrilogyTeleporterConfiguration(TeleporterConfiguration):
    skip_final_bosses: bool
    allow_unvisited_room_names: bool

    def get_credits_node(self) -> NodeIdentifier:
        match self.game:
            case RandovaniaGame.METROID_PRIME:
                return NodeIdentifier.create("End of Game", "Credits", "Event - Credits")
            case RandovaniaGame.METROID_PRIME_ECHOES:
                return NodeIdentifier.create("Temple Grounds", "Credits", "Event - Dark Samus 3 and 4")
            case _:
                raise ValueError(f"Unsupported game {self.game}")

    @property
    def can_use_unvisited_room_names(self) -> bool:
        return self.is_vanilla or self.allow_unvisited_room_names

    @property
    def static_teleporters(self) -> dict[NodeIdentifier, NodeIdentifier]:
        static = {}
        if self.game == RandovaniaGame.METROID_PRIME:
            credits_node = self.get_credits_node()
            if self.skip_final_bosses:
                crater = NodeIdentifier.create("Tallon Overworld", "Artifact Temple", "Teleporter to Impact Crater")
                static[crater] = credits_node
            elif self.mode in [
                TeleporterShuffleMode.ONE_WAY_TELEPORTER,
                TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
            ]:
                # We need to always have the possibility of having credits as a target.
                # On two-way, this is ensured by this teleporter always having this assignment.
                # On one-way-anywhere, this can be ensured as there is a dedicated credits target available.
                # But on these two one-way modes, there is not, so let's statically assign it to ensure that
                # one elevator always leads to credits.
                essence = NodeIdentifier.create("Impact Crater", "Metroid Prime Lair", "Teleporter to Credits")
                static[essence] = credits_node
        elif self.game == RandovaniaGame.METROID_PRIME_ECHOES:
            if self.skip_final_bosses:
                gateway = NodeIdentifier.create("Sky Temple Grounds", "Sky Temple Gateway", "Elevator to Sky Temple")
                static[gateway] = self.get_credits_node()
        else:
            raise ValueError(f"Unsupported game {self.game}")

        return static

    @property
    def valid_targets(self) -> list[NodeIdentifier]:
        original = super().valid_targets

        if self.mode in {
            TeleporterShuffleMode.ONE_WAY_TELEPORTER,
            TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
        }:
            game_description = default_database.game_description_for(self.game)
            region_list = game_description.region_list

            result = []
            for identifier in original:
                node = region_list.node_by_identifier(identifier)
                area = region_list.nodes_to_area(node)
                # Valid destinations must be valid starting areas
                if area.has_start_node():
                    result.append(identifier)
                # Hack for Metroid Prime 1, where the scripting for Metroid Prime Lair is dependent
                # on the previous room
                elif area.name == "Metroid Prime Lair":
                    result.append(NodeIdentifier.create("Impact Crater", "Subchamber Five", "Dock to Subchamber Four"))
            return result
        else:
            return original
