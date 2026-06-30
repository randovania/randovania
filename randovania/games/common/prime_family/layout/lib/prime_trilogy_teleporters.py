from __future__ import annotations

import dataclasses
from typing import override

from randovania.game_description import default_database
from randovania.game_description.db.area import Area
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.node import Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode, TeleporterTargetList


class PrimeTrilogyTeleporterTargetList(TeleporterTargetList):
    @override
    @classmethod
    def valid_teleporter_target(cls, area: Area, node: Node) -> bool:
        if any(node.name == "Save Station" for node in area.nodes):
            return False

        return super().valid_teleporter_target(area, node)


@dataclasses.dataclass(frozen=True)
class PrimeTrilogyTeleporterConfiguration(TeleporterConfiguration):
    # override parent field type
    excluded_targets: PrimeTrilogyTeleporterTargetList

    skip_final_bosses: bool

    @property
    def specific_valid_targets(self) -> dict[AreaIdentifier, NodeIdentifier]:
        """Some areas are weird and need specific overrides for `valid_targets`"""
        return {}

    @override
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

                if identifier.area_identifier in self.specific_valid_targets:
                    result.append(self.specific_valid_targets[identifier.area_identifier])

            return result

        else:
            return original
