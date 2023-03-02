import collections

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration
from randovania.gui.game_details.base_connection_details_tab import BaseConnectionDetailsTab
from randovania.interface_common.players_configuration import PlayersConfiguration


class PortalDetailsTab(BaseConnectionDetailsTab):
    def tab_title(self) -> str:
        return "Portals"

    @classmethod
    def should_appear_for(cls, configuration: EchoesConfiguration, all_patches: dict[int, GamePatches],
                          players: PlayersConfiguration) -> bool:
        return configuration.portal_rando

    def _fill_per_world_connections(self,
                                    per_world: dict[str, dict[str, str | dict[str, str]]],
                                    world_list: WorldList,
                                    patches: GamePatches,
                                    ):

        per_area = collections.defaultdict(lambda: collections.defaultdict(set))
        portal_count_in_area = collections.defaultdict(lambda: collections.defaultdict(int))

        for world in world_list.worlds:
            for area in world.areas:
                for node in area.nodes:
                    if isinstance(node, DockNode) and node.dock_type.short_name == "portal":
                        portal_count_in_area[world.name][area.name] += 1
                        destination = patches.get_dock_connection_for(node)
                        if area.in_dark_aether:
                            # All docks are two-way between light and dark aether right now
                            assert isinstance(destination, DockNode)
                            assert patches.get_dock_connection_for(destination) == node
                        else:
                            per_area[world.name][area.name].add(node)

        def name_for(target):
            target_world, target_area = world_list.world_and_area_by_area_identifier(
                target.identifier.area_location
            )
            target_name = target_area.name
            if portal_count_in_area[target_world.name][target_area.name] > 1:
                target_name += f" - {target.name}"
            return target_name

        for world_name, areas in per_area.items():
            for area_name, area_docks in areas.items():
                if not area_docks:
                    continue

                if len(area_docks) > 1:
                    per_world[world_name][area_name] = {}
                    for dock in sorted(area_docks, key=lambda it: it.name):
                        assert isinstance(dock, DockNode)
                        per_world[world_name][area_name][dock.name] = name_for(patches.get_dock_connection_for(dock))
                else:
                    dock = next(iter(area_docks))
                    assert isinstance(dock, DockNode)
                    per_world[world_name][area_name] = name_for(patches.get_dock_connection_for(dock))
