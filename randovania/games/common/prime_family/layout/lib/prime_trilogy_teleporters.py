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

    @property
    def can_use_unvisited_room_names(self) -> bool:
        return self.is_vanilla or self.allow_unvisited_room_names

    @property
    def static_teleporters(self) -> dict[NodeIdentifier, NodeIdentifier]:
        static = {}
        if self.skip_final_bosses:
            if self.game == RandovaniaGame.METROID_PRIME:
                crater = NodeIdentifier.create("Tallon Overworld", "Artifact Temple", "Teleporter to Impact Crater")
                static[crater] = NodeIdentifier.create("End of Game", "Credits", "Event - Credits")
            elif self.game == RandovaniaGame.METROID_PRIME_ECHOES:
                gateway = NodeIdentifier.create("Sky Temple Grounds", "Sky Temple Gateway", "Elevator to Sky Temple")
                static[gateway] = NodeIdentifier.create("Temple Grounds", "Credits", "Event - Dark Samus 3 and 4")
            else:
                raise ValueError(f"Unsupported skip_final_bosses and {self.game}")

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
