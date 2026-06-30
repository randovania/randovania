import dataclasses
from typing import override

from randovania.game_description.db.area import Area
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
    PrimeTrilogyTeleporterTargetList,
)
from randovania.layout.lib.teleporters import TeleporterShuffleMode


class PrimeTeleporterTargetList(PrimeTrilogyTeleporterTargetList):
    @override
    @classmethod
    def valid_teleporter_target(cls, area: Area, node: Node) -> bool:
        if area.name == "Credits" and node.name == "Event - Credits":
            return True

        return super().valid_teleporter_target(area, node)


@dataclasses.dataclass(frozen=True)
class PrimeTeleporterConfiguration(PrimeTrilogyTeleporterConfiguration):
    # override parent field type
    excluded_targets: PrimeTeleporterTargetList

    def get_credits_node(self) -> NodeIdentifier:
        return NodeIdentifier.create("End of Game", "Credits", "Event - Credits")

    @override
    @property
    def static_teleporters(self) -> dict[NodeIdentifier, NodeIdentifier]:
        static = {}
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

        return static

    @override
    @property
    def specific_valid_targets(self) -> dict[AreaIdentifier, NodeIdentifier]:
        targets = {}

        # Hack for Metroid Prime 1, where the scripting for Metroid Prime Lair is dependent
        # on the previous room
        lair = AreaIdentifier("Impact Crater", "Metroid Prime Lair")
        subchamber4_dock = NodeIdentifier.create("Impact Crater", "Subchamber Five", "Dock to Subchamber Four")
        targets[lair] = subchamber4_dock

        return targets
