from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.games.prime2 import dark_aether_helper
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.interface_common.players_configuration import PlayersConfiguration
    from randovania.layout.base.base_configuration import BaseConfiguration


class PortalDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        return "Portals"

    @classmethod
    def should_appear_for(
        cls, configuration: BaseConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        assert isinstance(configuration, EchoesConfiguration)
        return configuration.portal_rando

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        region_list: RegionList,
        patches: GamePatches,
    ) -> None:
        per_area: collections.defaultdict[str, collections.defaultdict[str, set[DockNode]]] = collections.defaultdict(
            lambda: collections.defaultdict(set)
        )
        portal_count_in_area: collections.defaultdict[str, collections.defaultdict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int)
        )

        for region, area, node in region_list.all_regions_areas_nodes:
            if isinstance(node, DockNode) and node.dock_type.short_name == "portal":
                portal_count_in_area[region.name][area.name] += 1
                destination = patches.get_dock_connection_for(node)
                if dark_aether_helper.is_region_light(region):
                    per_area[region.name][area.name].add(node)
                else:
                    # All docks are two-way between light and dark aether right now
                    assert isinstance(destination, DockNode)
                    assert patches.get_dock_connection_for(destination) == node

        def name_for(target: Node) -> str:
            target_region, target_area = region_list.region_and_area_by_area_identifier(
                target.identifier.area_identifier
            )
            target_name = target_area.name
            if portal_count_in_area[target_region.name][target_area.name] > 1:
                target_name += f" - {target.name}"
            return target_name

        for region_name, areas in per_area.items():
            for area_name, area_docks in areas.items():
                if not area_docks:
                    continue

                if len(area_docks) > 1:
                    per_region[region_name][area_name] = {}
                    for dock in sorted(area_docks, key=lambda it: it.name):
                        assert isinstance(dock, DockNode)
                        obj = per_region[region_name][area_name]
                        assert isinstance(obj, dict)
                        obj[dock.name] = name_for(patches.get_dock_connection_for(dock))
                else:
                    dock = next(iter(area_docks))
                    assert isinstance(dock, DockNode)
                    per_region[region_name][area_name] = name_for(patches.get_dock_connection_for(dock))
