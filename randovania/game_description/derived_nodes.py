import copy
import dataclasses

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.area import Area
from randovania.game_description.world.world_list import WorldList


def remove_inactive_layers(game: GameDescription, active_layers: set[str]) -> GameDescription:
    if unknown_layers := active_layers - set(game.layers):
        raise ValueError(f"Unknown layers: {unknown_layers}")

    worlds = []

    for world in game.world_list.worlds:
        areas = []
        for area in world.areas:
            nodes = copy.copy(area.nodes)
            connections = {
                node: copy.copy(connection) for node, connection in area.connections.items()
            }
            has_default_node = area.default_node is not None

            for node in area.nodes:
                if set(node.layers).isdisjoint(active_layers):
                    nodes.remove(node)
                    connections.pop(node, None)
                    for connection in connections.values():
                        connection.pop(node, None)

                    if area.default_node == node.name:
                        has_default_node = False

            areas.append(Area(
                name=area.name,
                default_node=area.default_node if has_default_node else None,
                valid_starting_location=area.valid_starting_location,
                nodes=nodes,
                connections=connections,
                extra=area.extra,
            ))

        worlds.append(dataclasses.replace(world, areas=areas))

    return GameDescription(
        game=game.game,
        resource_database=game.resource_database,
        layers=game.layers,
        dock_weakness_database=game.dock_weakness_database,
        world_list=WorldList(worlds),
        victory_condition=game.victory_condition,
        starting_location=game.starting_location,
        initial_states=game.initial_states,
        minimal_logic=game.minimal_logic,
    )
