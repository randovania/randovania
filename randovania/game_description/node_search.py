from typing import Dict, Optional

import networkx

from randovania.game_description.area import Area
from randovania.game_description.node import Node, DockNode, TeleporterNode, PickupNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList


def distances_to_node(world_list: WorldList, starting_node: Node,
                      cutoff: Optional[int] = None) -> Dict[Area, int]:
    """
    Compute the shortest distance from a node to all reachable areas.
    :param world_list:
    :param starting_node:
    :param cutoff: Exclude areas with a length longer that cutoff.
    :return: Dict keyed by area to shortest distance to starting_node.
    """
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

    return networkx.single_source_shortest_path_length(g, world_list.nodes_to_area(starting_node), cutoff)


def pickup_index_to_node(world_list: WorldList, index: PickupIndex) -> PickupNode:
    for node in world_list.all_nodes:
        if isinstance(node, PickupNode) and node.pickup_index == index:
            return node
    raise ValueError(f"PickupNode with {index} not found.")
