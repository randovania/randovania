from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.pickup_node import PickupNode

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.dock import DockType
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.pickup_index import PickupIndex


def distances_to_node(
    game_view: GameDatabaseView,
    starting_node: Node,
    dock_types_to_ignore: list[DockType],
    *,
    cutoff: int | None = None,
    patches: GamePatches | None = None,
) -> dict[Area, int]:
    """
    Compute the shortest distance from a node to all reachable areas.
    :param game_view:
    :param starting_node:
    :param dock_types_to_ignore:
    :param cutoff: Exclude areas with a length longer that cutoff.
    :param patches:
    :return: Dict keyed by area to shortest distance to starting_node.
    """
    import networkx

    g = networkx.DiGraph()

    if patches is None:

        def get_dock_connection_for(n: DockNode) -> NodeIdentifier:
            return n.default_connection

    else:

        def get_dock_connection_for(n: DockNode) -> NodeIdentifier:
            return patches.get_dock_connection_for(n).identifier

    node_to_area = {}

    all_pairs = []
    last_pair: tuple[Region, Area] | None = None
    for region, area, node in game_view.node_iterator():
        node_to_area[node.node_index] = area

        new_pair = (region, area)
        if new_pair == last_pair:
            continue

        last_pair = new_pair
        g.add_node(area)
        all_pairs.append(new_pair)

    for region, area in all_pairs:
        new_areas = set()
        for node in area.nodes:
            connection: NodeIdentifier | None = None
            if isinstance(node, DockNode) and node.dock_type not in dock_types_to_ignore:
                connection = get_dock_connection_for(node)

            if connection is not None:
                new_areas.add(node_to_area[game_view.node_by_identifier(connection).node_index])

        for next_area in new_areas:
            g.add_edge(area, next_area)

    return networkx.single_source_shortest_path_length(g, node_to_area[starting_node.node_index], cutoff)


def pickup_index_to_node(region_list: RegionList, index: PickupIndex) -> PickupNode:
    for node in region_list.iterate_nodes_of_type(PickupNode):
        if node.pickup_index == index:
            return node
    raise ValueError(f"PickupNode with {index} not found.")
