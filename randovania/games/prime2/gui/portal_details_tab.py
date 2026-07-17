from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2 import dark_aether_helper
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration


class PortalDetailsTab(BaseConnectionDetailsTab[EchoesOPRConfiguration]):
    def tab_title(self) -> str:
        return "Portals"

    @classmethod
    def should_appear_for(
        cls, configuration: EchoesOPRConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return configuration.portal_rando

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        game: GameDatabaseView,
        patches: GamePatches,
    ) -> None:
        per_area: collections.defaultdict[str, collections.defaultdict[str, set[DockNode]]] = collections.defaultdict(
            lambda: collections.defaultdict(set)
        )
        portal_count_in_area: collections.defaultdict[str, collections.defaultdict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int)
        )

        for region, area, node in game.iterate_nodes_of_type(DockNode):
            if node.dock_type.short_name != "portal":
                continue

            portal_count_in_area[region.name][area.name] += 1
            destination = game.node_by_identifier(patches.get_dock_connection_for(node))
            if dark_aether_helper.is_region_light(region):
                per_area[region.name][area.name].add(node)
            else:
                # All docks are two-way between light and dark aether right now
                assert isinstance(destination, DockNode)
                assert game.node_by_identifier(patches.get_dock_connection_for(destination)) == node

        def name_for(target: NodeIdentifier) -> str:
            target_name = target.area
            if portal_count_in_area[target.region][target.area] > 1:
                target_name += f" - {target.node}"
            return target_name

        for region_name, areas in per_area.items():
            for area_name, area_docks in areas.items():
                if not area_docks:
                    continue

                if len(area_docks) > 1:
                    per_region[region_name][area_name] = {
                        dock.name: name_for(patches.get_dock_connection_for(dock))
                        for dock in sorted(area_docks, key=lambda it: it.name)
                    }
                else:
                    dock = next(iter(area_docks))
                    per_region[region_name][area_name] = name_for(patches.get_dock_connection_for(dock))
