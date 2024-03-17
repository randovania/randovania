from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description import default_database
from randovania.game_description.db.dock_node import DockNode
from randovania.layout.lib.teleporters import TeleporterConfiguration, TeleporterShuffleMode

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier


@dataclasses.dataclass(frozen=True)
class AM2RTeleporterConfiguration(TeleporterConfiguration):
    # AM2R has only save stations as start nodes in the db. Pipes are no start nodes but
    # are valid targets and also the only valid targets. Preset settings makes sure
    # that nothing else is selected
    @property
    def valid_targets(self) -> list[NodeIdentifier]:
        if self.mode in {
            TeleporterShuffleMode.ONE_WAY_TELEPORTER,
            TeleporterShuffleMode.ONE_WAY_TELEPORTER_REPLACEMENT,
        }:
            game_description = default_database.game_description_for(self.game)
            teleporter_dock_types = game_description.dock_weakness_database.all_teleporter_dock_types
            region_list = game_description.region_list

            result = []
            for identifier in self.editable_teleporters:
                node = region_list.node_by_identifier(identifier)
                if isinstance(node, DockNode) and node.dock_type in teleporter_dock_types:
                    result.append(identifier)
            return result
        else:
            return []
