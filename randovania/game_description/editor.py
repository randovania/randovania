from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.node_requirement import NodeRequirement

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node, NodeIndex
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement


def replace_identifiers_in_requirement(
    requirement: Requirement, replacer: Callable[[NodeIdentifier], NodeIdentifier]
) -> Requirement:
    """
    Applies the replacer function to every NodeRequirement recursively nested in requirement.
    """
    if isinstance(requirement, RequirementArrayBase):
        return type(requirement)(
            (replace_identifiers_in_requirement(it, replacer) for it in requirement.items), comment=requirement.comment
        )
    elif isinstance(requirement, NodeRequirement):
        return NodeRequirement(replacer(requirement.node_identifier))
    else:
        return requirement


class Editor:
    def __init__(self, game: GameDescription):
        self.game = game
        self.next_node_index = len(game.region_list.all_nodes)

    def new_node_index(self) -> NodeIndex:
        result = self.next_node_index
        self.next_node_index += 1
        return result

    def edit_connections(self, area: Area, from_node: Node, target_node: Node, requirement: Requirement | None) -> None:
        current_connections = area.connections[from_node]

        if requirement is None:
            del area.connections[from_node][target_node]
        else:
            area.connections[from_node][target_node] = requirement

        area.connections[from_node] = {
            node: current_connections[node] for node in area.nodes if node in current_connections
        }

    def add_node(self, area: Area, node: Node) -> None:
        if area.node_with_name(node.name) is not None:
            raise ValueError(f"A node named {node.name} already exists.")
        area.nodes.append(node)
        area.connections[node] = {}
        area.clear_dock_cache()
        self.game.region_list.invalidate_node_cache()

    def remove_node(self, area: Area, node: Node) -> None:
        area.nodes.remove(node)
        area.connections.pop(node, None)
        for connection in area.connections.values():
            connection.pop(node, None)
        area.clear_dock_cache()

        self.game.region_list.invalidate_node_cache()

        if isinstance(node, DockNode):
            self.remove_node(area, node.lock_node)

    def replace_node(self, area: Area, old_node: Node, new_node: Node) -> None:
        def sub(n: Node) -> Node:
            return new_node if n == old_node else n

        if old_node not in area.nodes:
            raise ValueError(
                "Given {} does does not belong to {}{}".format(
                    old_node.name,
                    area.name,
                    (
                        ", but the area contains a node with that name."
                        if area.node_with_name(old_node.name) is not None
                        else "."
                    ),
                )
            )

        if old_node.name != new_node.name and area.node_with_name(new_node.name) is not None:
            raise ValueError(f"A node named {new_node.name} already exists.")

        old_lock_identifier = None
        if isinstance(old_node, DockNode):
            old_lock_identifier = old_node.lock_node.identifier
            self.remove_node(area, old_node.lock_node)

        old_identifier = old_node.identifier
        self.replace_references_to_node_identifier(
            old_identifier,
            old_identifier.renamed(new_node.name),
        )

        area.nodes[area.nodes.index(old_node)] = new_node

        new_connections = {
            sub(source_node): {sub(target_node): requirements for target_node, requirements in connection.items()}
            for source_node, connection in area.connections.items()
        }
        area.connections.clear()
        area.connections.update(new_connections)
        if area.default_node == old_node.name:
            object.__setattr__(area, "default_node", new_node.name)
        area.clear_dock_cache()

        if isinstance(new_node, DockNode):
            new_lock_node = DockLockNode.create_from_dock(new_node, self.new_node_index(), self.game.resource_database)
            self.add_node(area, new_lock_node)

            if isinstance(old_node, DockNode):
                assert old_lock_identifier is not None
                self.replace_references_to_node_identifier(
                    old_lock_identifier,
                    new_lock_node.identifier,
                )

        self.game.region_list.invalidate_node_cache()

    def rename_node(self, area: Area, node: Node, new_name: str) -> None:
        self.replace_node(area, node, dataclasses.replace(node, identifier=node.identifier.renamed(new_name)))

    def rename_area(self, current_area: Area, new_name: str) -> None:
        if current_area.name == new_name:
            return

        current_region = self.game.region_list.region_with_area(current_area)

        def identifier_replacer(old: NodeIdentifier) -> NodeIdentifier:
            if (old.region, old.area) == (current_region.name, current_area.name):
                return NodeIdentifier.create(
                    old.region,
                    new_name,
                    old.node,
                )
            else:
                return old

        self.replace_identifiers(identifier_replacer)

        new_area = dataclasses.replace(current_area, name=new_name)
        current_region.areas[current_region.areas.index(current_area)] = new_area

        for node in new_area.nodes:
            self.replace_node(
                new_area, node, dataclasses.replace(node, identifier=identifier_replacer(node.identifier))
            )

        self.game.region_list.invalidate_node_cache()

    def replace_identifiers(self, replacer: Callable[[NodeIdentifier], NodeIdentifier]) -> None:
        """
        Applies the given replacer to all connections and templates in the database
        """
        # Templates
        for template_name, template in self.game.resource_database.requirement_template.items():
            new_requirement = replace_identifiers_in_requirement(template.requirement, replacer)
            if template.requirement != new_requirement:
                self.game.resource_database.requirement_template[template_name] = dataclasses.replace(
                    template,
                    requirement=new_requirement,
                )

        # Connections
        for area in self.game.region_list.all_areas:
            for connections in area.connections.values():
                for target, requirement in connections.items():
                    new_requirement = replace_identifiers_in_requirement(requirement, replacer)
                    if requirement != new_requirement:
                        connections[target] = new_requirement

        # Dock Nodes
        for region in self.game.region_list.regions:
            for area in region.areas:
                for i in range(len(area.nodes)):
                    node = area.nodes[i]
                    new_node = None

                    if isinstance(node, DockNode):
                        new_default = replacer(node.default_connection)
                        new_fields: dict = {}

                        if node.default_connection != new_default:
                            new_fields["identifier"] = node.identifier.renamed(
                                node.name.replace(node.default_connection.area, new_default.area),
                            )
                            new_fields["default_connection"] = new_default

                        if node.override_default_open_requirement is not None:
                            new_requirement = replace_identifiers_in_requirement(
                                node.override_default_open_requirement, replacer
                            )
                            if node.override_default_open_requirement != new_requirement:
                                new_fields["override_default_open_requirement"] = new_requirement

                        if node.override_default_lock_requirement is not None:
                            new_requirement = replace_identifiers_in_requirement(
                                node.override_default_lock_requirement, replacer
                            )
                            if node.override_default_lock_requirement != new_requirement:
                                new_fields["override_default_lock_requirement"] = new_requirement

                        if new_fields:
                            new_node = dataclasses.replace(node, **new_fields)

                    if new_node is not None:
                        self.replace_node(area, node, new_node)

    def replace_references_to_node_identifier(
        self,
        old_identifier: NodeIdentifier,
        new_identifier: NodeIdentifier,
    ) -> None:
        if old_identifier == new_identifier:
            return

        def identifier_replacer(old: NodeIdentifier) -> NodeIdentifier:
            if old == old_identifier:
                return new_identifier
            else:
                return old

        self.replace_identifiers(identifier_replacer)

    def move_node_from_area_to_area(self, old_area: Area, new_area: Area, node: Node) -> None:
        assert node in old_area.nodes

        if new_area.node_with_name(node.name) is not None:
            raise ValueError(f"New area {new_area.name} already contains a node named {node.name}")

        old_region = self.game.region_list.region_with_area(old_area)
        new_region = self.game.region_list.region_with_area(new_area)

        self.remove_node(old_area, node)
        self.add_node(new_area, node)
        self.replace_references_to_node_identifier(
            NodeIdentifier.create(old_region.name, old_area.name, node.name),
            NodeIdentifier.create(new_region.name, new_area.name, node.name),
        )
