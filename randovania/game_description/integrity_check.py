import re
from typing import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import EventNode, Node, PickupNode, DockNode, TeleporterNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList

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
        try:
            world_list.resolve_dock_connection(world, node.default_connection)
        except IndexError as e:
            yield f"'{node.name}' is a Dock Node, but connection {node.default_connection} is invalid: {e}"

    if isinstance(node, TeleporterNode):
        try:
            world_list.resolve_teleporter_connection(node.default_connection)
        except IndexError as e:
            yield f"'{node.name}' is a Teleporter Node, but connection {node.default_connection} is invalid: {e}"


def find_area_errors(world_list: WorldList, area: Area) -> Iterator[str]:
    for node in area.nodes:
        for error in find_node_errors(world_list, node):
            yield f"{area.name} - {error}"

    if area.default_node is not None and area.node_with_name(area.default_node) is None:
        yield f"'{area.name} has default node {area.default_node}, but no node with that name exists"


def find_world_errors(world_list: WorldList, world: World) -> Iterator[str]:
    for area in world.areas:
        for error in find_area_errors(world_list, area):
            yield f"{world.name} - {error}"


def find_database_errors(game: GameDescription) -> list[str]:
    result = []

    for world in game.world_list.worlds:
        result.extend(find_world_errors(game.world_list, world))

    return result
