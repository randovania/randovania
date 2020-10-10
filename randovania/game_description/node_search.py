from typing import Dict

import networkx

from randovania.game_description.area import Area
from randovania.game_description.node import Node, DockNode, TeleporterNode
from randovania.game_description.world_list import WorldList


def distances_to_node(world_list: WorldList, starting_node: Node) -> Dict[Area, int]:
    g = networkx.DiGraph()

    for area in world_list.all_areas:
        g.add_node(area)

    for world in world_list.worlds:
        for area in world.areas:
            new_areas = set()
            for node in area.nodes:
                if isinstance(node, DockNode):
                    new_areas.add(world.area_by_asset_id(node.default_connection.area_asset_id))
                elif isinstance(node, TeleporterNode):
                    new_areas.add(world_list.area_by_area_location(node.default_connection))

            for next_area in new_areas:
                g.add_edge(area, next_area)

    return networkx.single_source_shortest_path_length(g, world_list.nodes_to_area(starting_node))
