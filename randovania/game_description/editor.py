import dataclasses
from typing import Optional

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import Node, TeleporterNode, DockNode
from randovania.game_description.world.node_identifier import NodeIdentifier


class Editor:
    def __init__(self, game: GameDescription):
        self.game = game

    def edit_connections(self, area: Area, from_node: Node, target_node: Node, requirement: Optional[Requirement]):
        current_connections = area.connections[from_node]
        area.connections[from_node][target_node] = requirement
        if area.connections[from_node][target_node] is None:
            del area.connections[from_node][target_node]

        area.connections[from_node] = {
            node: current_connections[node]
            for node in area.nodes
            if node in current_connections
        }

    def add_node(self, area: Area, node: Node):
        area.nodes.append(node)
        area.connections[node] = {}
        area.clear_dock_cache()
        self.game.world_list.invalidate_node_cache()

    def remove_node(self, area: Area, node: Node):
        area.nodes.remove(node)
        area.connections.pop(node, None)
        for connection in area.connections.values():
            connection.pop(node, None)
        area.clear_dock_cache()

        self.game.world_list.invalidate_node_cache()

    def replace_node(self, area: Area, old_node: Node, new_node: Node):
        def sub(n: Node):
            return new_node if n == old_node else n

        area_node_list = area.nodes
        for i, node in enumerate(area_node_list):
            if node == old_node:
                area_node_list[i] = new_node

        new_connections = {
            sub(source_node): {
                sub(target_node): requirements
                for target_node, requirements in connection.items()
            }
            for source_node, connection in area.connections.items()
        }
        area.connections.clear()
        area.connections.update(new_connections)
        if area.default_node == old_node.name:
            object.__setattr__(area, "default_node", new_node.name)
        area.clear_dock_cache()

        self.game.world_list.invalidate_node_cache()

    def rename_area(self, current_area: Area, new_name: str):
        current_world = self.game.world_list.world_with_area(current_area)
        old_name = current_area.name
        old_identifier = self.game.world_list.identifier_for_area(current_area)
        new_identifier = dataclasses.replace(old_identifier, area_name=new_name)

        for world in self.game.world_list.worlds:
            for area in world.areas:
                for i in range(len(area.nodes)):
                    node = area.nodes[i]

                    new_node = None
                    if isinstance(node, TeleporterNode):
                        if node.default_connection == old_identifier:
                            new_node = dataclasses.replace(node,
                                                           name=node.name.replace(old_name, new_name),
                                                           default_connection=new_identifier)

                    elif isinstance(node, DockNode):
                        if world == current_world and node.default_connection.area_name == old_name:
                            new_node = dataclasses.replace(
                                node,
                                name=node.name.replace(old_name, new_name),
                                default_connection=NodeIdentifier.create(
                                    world_name=node.default_connection.world_name,
                                    area_name=new_name,
                                    node_name=node.default_connection.node_name,
                                ),
                            )

                    if new_node is not None:
                        self.replace_node(area, node, new_node)

        new_area = dataclasses.replace(current_area, name=new_name)
        current_world.areas[current_world.areas.index(current_area)] = new_area

        self.game.world_list.invalidate_node_cache()
