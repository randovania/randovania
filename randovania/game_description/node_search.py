from typing import Dict, Optional

import networkx

from randovania.game_description.world.area import Area
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node import Node, DockNode, TeleporterNode, PickupNode, ResourceNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.world.world_list import WorldList


def distances_to_node(world_list: WorldList, starting_node: Node,
                      *,
                      ignore_elevators: bool = True,
                      cutoff: Optional[int] = None,
                      patches: Optional[GamePatches] = None,
                      ) -> Dict[Area, int]:
    """
    Compute the shortest distance from a node to all reachable areas.
    :param world_list:
    :param starting_node:
    :param ignore_elevators:
    :param cutoff: Exclude areas with a length longer that cutoff.
    :param patches:
    :return: Dict keyed by area to shortest distance to starting_node.
    """
    g = networkx.DiGraph()

    dock_connections = patches.dock_connection if patches is not None else {}
    elevator_connections = patches.elevator_connection if patches is not None else {}

    for area in world_list.all_areas:
        g.add_node(area)

    for world in world_list.worlds:
        for area in world.areas:
            new_areas = set()
            for node in area.nodes:
                if isinstance(node, DockNode):
                    connection = dock_connections.get((area.area_asset_id, node.dock_index), node.default_connection)
                    if connection is not None:
                        new_areas.add(world.area_by_asset_id(connection.area_asset_id))

                elif isinstance(node, TeleporterNode) and not ignore_elevators:
                    connection = elevator_connections.get(node.teleporter, node.default_connection)
                    if connection is not None:
                        new_areas.add(world_list.area_by_area_location(connection))

            for next_area in new_areas:
                g.add_edge(area, next_area)

    return networkx.single_source_shortest_path_length(g, world_list.nodes_to_area(starting_node), cutoff)


def pickup_index_to_node(world_list: WorldList, index: PickupIndex) -> PickupNode:
    for node in world_list.all_nodes:
        if isinstance(node, PickupNode) and node.pickup_index == index:
            return node
    raise ValueError(f"PickupNode with {index} not found.")


def node_with_resource(world_list: WorldList, resource: ResourceInfo) -> ResourceNode:
    for node in world_list.all_nodes:
        if isinstance(node, ResourceNode) and node.resource() == resource:
            return node
    raise ValueError(f"ResourceNode with {resource} not found.")
