from __future__ import annotations

import dataclasses

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.layout.lib.teleporters import TeleporterConfiguration


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
                gateway = NodeIdentifier.create("Temple Grounds", "Sky Temple Gateway", "Elevator to Great Temple")
                static[gateway] = NodeIdentifier.create("Temple Grounds", "Credits", "Event - Dark Samus 3 and 4")
            else:
                raise ValueError(f"Unsupported skip_final_bosses and {self.game}")

        return static
