from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import Node
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world_list import WorldList


def distances_to_node(world_list: WorldList, starting_node: Node,
                      *,
                      ignore_elevators: bool = True,
                      cutoff: int | None = None,
                      patches: GamePatches | None = None,
                      ) -> dict[Area, int]:
    """
    Compute the shortest distance from a node to all reachable areas.
    :param world_list:
    :param starting_node:
    :param ignore_elevators:
    :param cutoff: Exclude areas with a length longer that cutoff.
    :param patches:
    :return: Dict keyed by area to shortest distance to starting_node.
    """
    import networkx
    g = networkx.DiGraph()

    if patches is None:
        def get_elevator_connection_for(n: TeleporterNode):
            return n.default_connection

        def get_dock_connection_for(n: DockNode):
            return n.default_connection
    else:
        get_elevator_connection_for = patches.get_elevator_connection_for

        def get_dock_connection_for(n: DockNode):
            return patches.get_dock_connection_for(n).identifier

    for area in world_list.all_areas:
        g.add_node(area)

    for world in world_list.worlds:
        for area in world.areas:
            new_areas = set()
            for node in area.nodes:
                connection = None
                if isinstance(node, DockNode):
                    connection = get_dock_connection_for(node).area_identifier

                elif isinstance(node, TeleporterNode) and not ignore_elevators:
                    connection = get_elevator_connection_for(node)

                if connection is not None:
                    new_areas.add(world_list.area_by_area_location(connection))

            for next_area in new_areas:
                g.add_edge(area, next_area)

    return networkx.single_source_shortest_path_length(g, world_list.nodes_to_area(starting_node), cutoff)


def pickup_index_to_node(world_list: WorldList, index: PickupIndex) -> PickupNode:
    for node in world_list.iterate_nodes():
        if isinstance(node, PickupNode) and node.pickup_index == index:
            return node
    raise ValueError(f"PickupNode with {index} not found.")
