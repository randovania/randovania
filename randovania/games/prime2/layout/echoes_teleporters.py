import dataclasses
from typing import override

from randovania.game_description.db.area import Area
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
    PrimeTrilogyTeleporterTargetList,
)


class EchoesTeleporterTargetList(PrimeTrilogyTeleporterTargetList):
    @override
    @classmethod
    def valid_teleporter_target(cls, area: Area, node: Node) -> bool:
        if area.name == "Credits" and node.name == "Event - Dark Samus 3 and 4":
            return True

        return super().valid_teleporter_target(area, node)


@dataclasses.dataclass(frozen=True)
class EchoesTeleporterConfiguration(PrimeTrilogyTeleporterConfiguration):
    # override parent field type
    excluded_targets: EchoesTeleporterTargetList

    @override
    @property
    def static_teleporters(self) -> dict[NodeIdentifier, NodeIdentifier]:
        static = {}

        if self.skip_final_bosses:
            gateway = NodeIdentifier.create("Sky Temple Grounds", "Sky Temple Gateway", "Elevator to Sky Temple")
            static[gateway] = NodeIdentifier.create("Temple Grounds", "Credits", "Event - Dark Samus 3 and 4")

        return static
