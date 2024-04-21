from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab

if TYPE_CHECKING:
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
    from randovania.interface_common.players_configuration import PlayersConfiguration


class PortalDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        return "Portals"

    @classmethod
    def should_appear_for(
        cls, configuration: EchoesConfiguration, all_patches: dict[int, GamePatches], players: PlayersConfiguration
    ) -> bool:
        return configuration.portal_rando

    def _fill_per_region_connections(
        self,
        per_region: dict[str, dict[str, str | dict[str, str]]],
        region_list: RegionList,
        patches: GamePatches,
    ):
        per_area = collections.defaultdict(lambda: collections.defaultdict(set))
        portal_count_in_area = collections.defaultdict(lambda: collections.defaultdict(int))

        for region, area, node in region_list.all_regions_areas_nodes:
            if isinstance(node, DockNode) and node.dock_type.short_name == "portal":
                portal_count_in_area[region.name][area.name] += 1
                destination = patches.get_dock_connection_for(node)
                if area.in_dark_aether:
                    # All docks are two-way between light and dark aether right now
                    assert isinstance(destination, DockNode)
                    assert patches.get_dock_connection_for(destination) == node
                else:
                    per_area[region.name][area.name].add(node)

        def name_for(target):
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
                        per_region[region_name][area_name][dock.name] = name_for(patches.get_dock_connection_for(dock))
                else:
                    dock = next(iter(area_docks))
                    assert isinstance(dock, DockNode)
                    per_region[region_name][area_name] = name_for(patches.get_dock_connection_for(dock))
