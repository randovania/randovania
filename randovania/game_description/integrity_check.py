from __future__ import annotations

import re
import typing
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.array_base import RequirementArrayBase
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_template import RequirementTemplate
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.layout.base.base_configuration import BaseConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.pickup_index import PickupIndex

pickup_node_re = re.compile(r"^Pickup (\d+ )?\(.*\)$")
dock_node_suffix_re = re.compile(r" \([^()]+?\)$")
layer_name_re = re.compile(r"[a-zA-Z0-9 _-]+")


def raw_expected_dock_names(
    dock_type: DockType, weakness: DockWeakness, connection: AreaIdentifier, source_region_name: str
) -> Iterator[str]:
    """
    Provides valid names for a node created with these fields. The first result is the recommended name.
    """
    expected_connector = "to"
    if weakness.requirement == Requirement.impossible() and weakness.name != "Not Determined":
        expected_connector = "from"
    target_area_str = f"{dock_type.long_name} {expected_connector} {connection.area}"
    target_region_str = f"{dock_type.long_name} {expected_connector} {connection.region}"
    if source_region_name != connection.region:
        yield target_region_str
    yield target_area_str


def expected_dock_names(node: DockNode) -> Iterator[str]:
    """
    Provides valid names for this node. The first result is the recommended name.
    """
    yield from raw_expected_dock_names(
        node.dock_type, node.default_dock_weakness, node.default_connection.area_identifier, node.identifier.region
    )


def docks_with_same_base_name(area: Area, expected_name: str) -> list[DockNode]:
    return [
        other
        for other in area.nodes
        if isinstance(other, DockNode)
        and any(
            expected == expected_name and other.name.startswith(expected) for expected in expected_dock_names(other)
        )
    ]


def dock_has_correct_name(area: Area, node: DockNode) -> bool:
    """

    :param area:
    :param node:
    :return: Check if the name matches the rules for how the node should be called
    """
    for expected_name in expected_dock_names(node):
        docks_same_base_name = docks_with_same_base_name(area, expected_name)

        if node.name.startswith(expected_name):
            if len(docks_same_base_name) > 1:
                m = dock_node_suffix_re.match(node.name[len(expected_name) :])
                if m is not None:
                    return True
            else:
                if node.name == expected_name:
                    return True

    return False


def find_node_errors(game: GameDescription, node: Node) -> Iterator[str]:
    region_list = game.region_list
    area = region_list.nodes_to_area(node)

    if invalid_layers := set(node.layers) - set(game.layers):
        yield f"{node.name} has unknown layers {invalid_layers}"

    if isinstance(node, EventNode):
        if not node.name.startswith("Event -"):
            yield f"{node.name} is an Event Node, but naming doesn't start with 'Event -'"

    elif node.name.startswith("Event -"):
        yield f"{node.name} is not an Event Node, but naming suggests it is"

    if isinstance(node, PickupNode):
        if pickup_node_re.match(node.name) is None:
            yield f"{node.name} is a Pickup Node, but naming doesn't match 'Pickup (...)'"
    elif pickup_node_re.match(node.name) is not None:
        yield f"{node.name} is not a Pickup Node, but naming matches 'Pickup (...)'"

    if isinstance(node, DockNode):
        valid_name = dock_has_correct_name(area, node)

        if not valid_name:
            options = [
                name + (" (...)" if len(docks_with_same_base_name(area, name)) > 1 else "")
                for name in expected_dock_names(node)
            ]
            expression_msg = " or ".join(f"'{opt}'" for opt in options)
            yield f"{node.name} should be named {expression_msg}"

        other_node = None
        try:
            other_node = region_list.node_by_identifier(node.default_connection)
        except (ValueError, KeyError) as e:
            yield f"{node.name} is a Dock Node, but connection '{node.default_connection}' is invalid: {e}"

        if other_node is not None:
            if isinstance(other_node, DockNode):
                if other_node.default_connection != node.identifier:
                    yield (
                        f"{node.name} connects to '{node.default_connection}', but that dock connects "
                        f"to '{other_node.default_connection}' instead."
                    )

    elif any(
        re.match(rf"{dock_type.long_name}\s*(to|from)", node.name)
        for dock_type in game.dock_weakness_database.dock_types
    ):
        yield f"{node.name} is not a Dock Node, naming suggests it should be."


def find_area_errors(game: GameDescription, area: Area) -> Iterator[str]:
    nodes_with_paths_in: set[Node] = set()
    for node in area.nodes:
        nodes_with_paths_in.update(area.connections[node].keys())

        for error in find_node_errors(game, node):
            yield f"{area.name}/{error}"

        if node in area.connections.get(node, {}):
            yield f"{area.name}/{node.name} has a connection to itself"

    # make sure only one start node exists per area like before refacor. this can be removed later if a game supports it
    start_nodes = area.get_start_nodes()
    if len(start_nodes) > 1 and not game.game.data.multiple_start_nodes_per_area:
        names = [node.name for node in start_nodes]
        yield f"{area.name} has multiple valid start nodes {names}, but is not allowed for {game.game.long_name}"

    for node in area.nodes:
        if isinstance(node, DockNode) or area.connections[node]:
            continue

        # FIXME: cannot implement this for PickupNodes because their resource gain depends on GamePatches
        if isinstance(node, EventNode):
            # if this node would satisfy the victory condition, it does not need outgoing connections
            current = ResourceCollection.with_database(game.resource_database)
            current.set_resource(node.event, 1)
            if game.victory_condition.satisfied(game.create_node_context(current), 0):
                continue

        if node in nodes_with_paths_in:
            yield f"{area.name} - '{node.name}': Node has paths in, but no connections out."


def find_region_errors(game: GameDescription, region: Region) -> Iterator[str]:
    for area in region.areas:
        for error in find_area_errors(game, area):
            yield f"{region.name}/{error}"


def find_invalid_strongly_connected_components(game: GameDescription) -> Iterator[str]:
    import networkx  # type: ignore

    graph = networkx.DiGraph()

    for node in game.region_list.iterate_nodes():
        if isinstance(node, DockLockNode):
            continue
        graph.add_node(node)

    context = NodeContext(
        patches=GamePatches.create_from_game(game, 0, typing.cast(BaseConfiguration, None)),
        current_resources=ResourceCollection.with_database(game.resource_database),
        database=game.resource_database,
        node_provider=game.region_list,
    )

    for node in game.region_list.iterate_nodes():
        if node not in graph:
            continue

        try:
            for other, req in game.region_list.potential_nodes_from(node, context):
                if other not in graph:
                    continue

                if req != Requirement.impossible():
                    graph.add_edge(node, other)

        except KeyError:
            # Broken docks
            continue

    starting_node = game.region_list.node_by_identifier(game.starting_location)

    for strong_comp in networkx.strongly_connected_components(graph):
        components: set[Node] = strong_comp

        # The starting location determines the default component
        if starting_node in components:
            continue

        if any(node.extra.get("different_strongly_connected_component", False) for node in components):
            continue

        if len(components) == 1:
            node = next(iter(components))

            # If the component is a single node which is the default node of its area, allow it
            area = game.region_list.nodes_to_area(node)
            if area.default_node == node.name:
                continue

            # We accept nodes that have no paths out or in.
            if not graph.in_edges(node) and not graph.edges(node):
                continue

        names = sorted(game.region_list.node_name(node, with_region=True) for node in strong_comp)
        yield f"Unknown strongly connected component detected containing {len(names)} nodes:\n{names}"


def find_recursive_templates(game: GameDescription) -> Iterator[str]:
    db = game.resource_database

    def recurse(last_name: str, req: Requirement, seen: list[str]) -> str | None:
        if isinstance(req, RequirementArrayBase):
            for it in req.items:
                msg = recurse(last_name, it, seen)
                if msg is not None:
                    return msg
        elif isinstance(req, RequirementTemplate):
            new_seen = [*seen, req.template_name]

            if req.template_name in seen:
                return f"Loop detected: {new_seen}"

            return recurse(req.template_name, db.requirement_template[req.template_name].requirement, new_seen)

        return None

    for root_template, template in db.requirement_template.items():
        msg = recurse(root_template, template.requirement, [root_template])
        if msg is not None:
            yield f"Checking {root_template}: {msg}"


def find_duplicated_pickup_index(region_list: RegionList) -> Iterator[str]:
    known_indices: dict[PickupIndex, str] = {}

    for node in region_list.all_nodes:
        if isinstance(node, PickupNode):
            name = region_list.node_name(node, with_region=True, distinguish_dark_aether=True)
            if node.pickup_index in known_indices:
                yield (
                    f"{name} has {node.pickup_index}, " f"but it was already used in {known_indices[node.pickup_index]}"
                )
            else:
                known_indices[node.pickup_index] = name


def find_database_errors(game: GameDescription) -> list[str]:
    result = []

    for layer in game.layers:
        if layer_name_re.match(layer) is None:
            result.append(f"Layer '{layer}' doesn't match {layer_name_re.pattern}")

    for region in game.region_list.regions:
        result.extend(find_region_errors(game, region))
    result.extend(find_invalid_strongly_connected_components(game))
    result.extend(find_recursive_templates(game))
    result.extend(find_duplicated_pickup_index(game.region_list))

    return result
