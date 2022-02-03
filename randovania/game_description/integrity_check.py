import re
from typing import Iterator, Optional

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.resource_info import convert_resource_gain_to_current_resources
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock import DockWeakness, DockType
from randovania.game_description.world.node import EventNode, Node, PickupNode, DockNode, TeleporterNode
from randovania.game_description.world.world import World

pickup_node_re = re.compile(r"^Pickup (\d+ )?\(.*\)$")
dock_node_re = re.compile(r"(.+?) (to|from) (.+?)( \(.*\))?$")
dock_node_suffix_re = re.compile(r"(.+?)( \([^()]+?\))$")


def base_dock_name_raw(dock_type: DockType, weakness: DockWeakness, connection: AreaIdentifier) -> str:
    expected_connector = "to"
    if weakness.requirement == Requirement.impossible() and weakness.name != "Not Determined":
        expected_connector = "from"
    return f"{dock_type.long_name} {expected_connector} {connection.area_name}"


def base_dock_name(node: DockNode) -> str:
    return base_dock_name_raw(node.dock_type, node.default_dock_weakness, node.default_connection.area_identifier)


def docks_with_same_base_name(area: Area, expected_name: str) -> list[DockNode]:
    return [
        other for other in area.nodes
        if isinstance(other, DockNode) and base_dock_name(other) == expected_name
    ]


def dock_has_correct_name(area: Area, node: DockNode) -> tuple[bool, Optional[str]]:
    """

    :param area:
    :param node:
    :return: bool, True indicates the name is good. string, for a suffix recommendation or None if unknown
    """
    expected_name = base_dock_name(node)
    docks_to_same_target = docks_with_same_base_name(area, expected_name)

    if len(docks_to_same_target) > 1:
        m = dock_node_suffix_re.match(node.name)
        if m is None:
            return False, None
        else:
            return m.group(1) == expected_name, m.group(2)
    else:
        return expected_name == node.name, ""


def find_node_errors(game: GameDescription, node: Node) -> Iterator[str]:
    world_list = game.world_list
    area = world_list.nodes_to_area(node)

    if isinstance(node, EventNode):
        if not node.name.startswith("Event -"):
            yield f"'{node.name}' is an Event Node, but naming doesn't start with 'Event -'"

    elif node.name.startswith("Event -"):
        yield f"'{node.name}' is not an Event Node, but naming suggests it is"

    if isinstance(node, PickupNode):
        if pickup_node_re.match(node.name) is None:
            yield f"'{node.name}' is a Pickup Node, but naming doesn't match 'Pickup (...)'"
    elif pickup_node_re.match(node.name) is not None:
        yield f"'{node.name}' is not a Pickup Node, but naming matches 'Pickup (...)'"

    if isinstance(node, DockNode):
        valid_name, suffix = dock_has_correct_name(area, node)
        expression_msg = base_dock_name(node)
        if suffix != "":
            expression_msg += " (...)"

        if not valid_name:
            yield f"'{node.name}' should be named '{expression_msg}'"

        other_node = None
        try:
            other_node = world_list.node_by_identifier(node.default_connection)
        except ValueError as e:
            yield f"'{node.name}' is a Dock Node, but connection '{node.default_connection}' is invalid: {e}"

        if other_node is not None:
            if isinstance(other_node, DockNode):
                if other_node.default_connection != world_list.identifier_for_node(node):
                    yield (f"'{node.name}' connects to '{node.default_connection}', but that dock connects "
                           f"to '{other_node.default_connection}' instead.")
            else:
                yield f"'{node.name}' connects to '{node.default_connection}' which is not a DockNode"

    elif any(node.name.startswith(dock_type.long_name) for dock_type in game.dock_weakness_database.dock_types):
        yield f"'{node.name}' is not a Dock Node, naming suggests it should be."

    if isinstance(node, TeleporterNode):
        try:
            world_list.resolve_teleporter_connection(node.default_connection)
        except IndexError as e:
            yield f"'{node.name}' is a Teleporter Node, but connection {node.default_connection} is invalid: {e}"


def find_area_errors(game: GameDescription, area: Area) -> Iterator[str]:
    nodes_with_paths_in = set()
    for node in area.nodes:
        nodes_with_paths_in.update(area.connections[node].keys())

        for error in find_node_errors(game, node):
            yield f"{area.name} - {error}"

        if node in area.connections.get(node, {}):
            yield f"{area.name} - Node '{node.name}' has a connection to itself"

    if area.default_node is not None and area.node_with_name(area.default_node) is None:
        yield f"{area.name} has default node {area.default_node}, but no node with that name exists"

    # elif area.default_node is not None:
    #     nodes_with_paths_in.add(area.node_with_name(area.default_node))

    for node in area.nodes:
        if isinstance(node, (TeleporterNode, DockNode)) or area.connections[node]:
            continue

        # FIXME: cannot implement this for PickupNodes because their resource gain depends on GamePatches
        if isinstance(node, EventNode):
            # if this node would satisfy the victory condition, it does not need outgoing connections
            current = convert_resource_gain_to_current_resources(node.resource_gain_on_collect(None))
            if game.victory_condition.satisfied(current, 0, game.resource_database):
                continue

        if node in nodes_with_paths_in:
            yield f"{area.name} - '{node.name}': Node has paths in, but no connections out."


def find_world_errors(game: GameDescription, world: World) -> Iterator[str]:
    for area in world.areas:
        for error in find_area_errors(game, area):
            yield f"{world.name} - {error}"


def find_invalid_strongly_connected_components(game: GameDescription) -> Iterator[str]:
    import networkx
    graph = networkx.DiGraph()

    for node in game.world_list.all_nodes:
        graph.add_node(node)

    for node in game.world_list.all_nodes:
        for other, req in game.world_list.potential_nodes_from(node, game.create_game_patches()):
            if req != Requirement.impossible():
                graph.add_edge(node, other)

    starting_node = game.world_list.resolve_teleporter_connection(game.starting_location)

    for strong_comp in networkx.strongly_connected_components(graph):
        components: set[Node] = strong_comp

        # The starting location determines the default component
        if starting_node in components:
            continue

        if any(node.extra.get("different_strongly_connected_component", False) for node in components):
            continue

        if len(components) == 1:
            node = next(iter(components))

            # If the component is a single node which is the default node of it's area, allow it
            area = game.world_list.nodes_to_area(node)
            if area.default_node == node.name:
                continue

            # We accept nodes that have no paths out or in.
            if not graph.in_edges(node) and not graph.edges(node):
                continue

        names = sorted(
            game.world_list.node_name(node, with_world=True)
            for node in strong_comp
        )
        yield "Unknown strongly connected component detected containing {} nodes:\n{}".format(len(names), names)


def find_database_errors(game: GameDescription) -> list[str]:
    result = []

    for world in game.world_list.worlds:
        result.extend(find_world_errors(game, world))
    result.extend(find_invalid_strongly_connected_components(game))

    return result
