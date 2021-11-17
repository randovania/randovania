from typing import Iterator

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import EventNode, Node
from randovania.game_description.world.world import World


def find_node_errors(node: Node) -> Iterator[str]:
    if isinstance(node, EventNode):
        if not node.name.startswith("Event -"):
            yield f"'{node.name}' is an Event Node, but naming doesn't start with 'Event -'"

    elif node.name.startswith("Event -"):
        yield f"'{node.name}' is not an Event Node, but naming suggests it is."


def find_area_errors(area: Area) -> Iterator[str]:
    for node in area.nodes:
        for error in find_node_errors(node):
            yield f"{area.name} - {error}"


def find_world_errors(world: World) -> Iterator[str]:
    for area in world.areas:
        for error in find_area_errors(area):
            yield f"{world.name} - {error}"


def find_database_errors(game: GameDescription) -> list[str]:
    result = []

    for world in game.world_list.worlds:
        result.extend(find_world_errors(world))

    return result
