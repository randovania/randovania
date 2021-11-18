import re
from typing import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock import DockType
from randovania.game_description.world.node import EventNode, Node, PickupNode, DockNode, TeleporterNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.lib.enum_lib import iterate_enum

pickup_node_re = re.compile(r"^Pickup (\d+ )?\(.*\)$")


def find_node_errors(world_list: WorldList, node: Node) -> Iterator[str]:
    world = world_list.nodes_to_world(node)

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
        # dock_type = node.default_dock_weakness.dock_type
        # expression = dock_type.node_name_prefix + " (to|from) "
        # m = re.match(expression, node.name)
        # if m is None and dock_type != DockType.OTHER:
        #     yield f"'{node.name}' is a Dock Node of type {dock_type}, but name does not match '{expression}'"
        # else:
        #     other_area = m.group(1)
        #     if other_area != node.default_connection.area_name:
        #         yield (f"'{node.name}' name suggests a connection to {other_area}, but it "
        #                f"connects to {node.default_connection.area_name}")

        try:
            world_list.resolve_dock_connection(world, node.default_connection)
        except IndexError as e:
            yield f"'{node.name}' is a Dock Node, but connection {node.default_connection} is invalid: {e}"

    elif any(node.name.startswith(dock_type.node_name_prefix) for dock_type in iterate_enum(DockType)):
        yield f"'{node.name}' is not a Dock Node, naming suggests it should be."

    if isinstance(node, TeleporterNode):
        try:
            world_list.resolve_teleporter_connection(node.default_connection)
        except IndexError as e:
            yield f"'{node.name}' is a Teleporter Node, but connection {node.default_connection} is invalid: {e}"


def find_area_errors(world_list: WorldList, area: Area) -> Iterator[str]:
    nodes_with_paths_in = set()
    for node in area.nodes:
        nodes_with_paths_in.update(area.connections[node].keys())

        for error in find_node_errors(world_list, node):
            yield f"{area.name} - {error}"

    if area.default_node is not None and area.node_with_name(area.default_node) is None:
        yield f"'{area.name} has default node {area.default_node}, but no node with that name exists"

    # elif area.default_node is not None:
    #     nodes_with_paths_in.add(area.node_with_name(area.default_node))

    for node in area.nodes:
        if isinstance(node, (TeleporterNode, DockNode)) or area.connections[node]:
            continue

        if node in nodes_with_paths_in:
            yield f"'{area.name} - {node.name}: Node has paths in, but no connections out."


def find_world_errors(world_list: WorldList, world: World) -> Iterator[str]:
    for area in world.areas:
        for error in find_area_errors(world_list, area):
            yield f"{world.name} - {error}"


def find_database_errors(game: GameDescription) -> list[str]:
    result = []

    for world in game.world_list.worlds:
        result.extend(find_world_errors(game.world_list, world))

    return result
