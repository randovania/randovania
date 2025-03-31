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
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_collection import ResourceCollection

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.layout.base.base_configuration import BaseConfiguration

pickup_node_re = re.compile(r"^Pickup (\d+ )?\(.*\)$")
dock_node_suffix_re = re.compile(r" \([^()]+?\)$")
layer_name_re = re.compile(r"[a-zA-Z0-9 _-]+")


def _create_node_context(game: GameDescription) -> NodeContext:
    return NodeContext(
        patches=GamePatches.create_from_game(game, 0, typing.cast("BaseConfiguration", None)),
        current_resources=ResourceCollection.with_database(game.resource_database),
        database=game.resource_database,
        node_provider=game.region_list,
    )


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
        yield from check_for_redundant_hint_features(area, node)
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

    yield from check_for_unnormalized_hint_features(area)


def find_region_errors(game: GameDescription, region: Region) -> Iterator[str]:
    for area in region.areas:
        for error in find_area_errors(game, area):
            yield f"{region.name}/{error}"


def find_invalid_strongly_connected_components(game: GameDescription) -> Iterator[str]:
    import networkx

    graph = networkx.DiGraph()

    for node in game.region_list.iterate_nodes():
        if isinstance(node, DockLockNode):
            continue
        graph.add_node(node)

    context = _create_node_context(game)

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
                yield (f"{name} has {node.pickup_index}, but it was already used in {known_indices[node.pickup_index]}")
            else:
                known_indices[node.pickup_index] = name


def _needed_resources_partly_satisfied(
    req: Requirement, resources: tuple[str, tuple[str, ...]], context: NodeContext, req_cache: dict
) -> bool:
    if req in req_cache:
        req_set = req_cache[req]
    else:
        req_set = req.as_set(context)
        req_cache[req] = req_set

    counter = 0
    res_key = resources[0]
    res_values = resources[1]
    for alternative in req_set.alternatives:
        # Either the key must not be present, or the key is present with all values.
        if not any(res_key == item.resource.short_name for item in alternative.values()):
            counter += 1
        elif all(any(resource == item.resource.short_name for item in alternative.values()) for resource in res_values):
            counter += 1

    return counter != len(req_set.alternatives)


def _does_requirement_contain_resource(req: Requirement, resource: str) -> bool:
    if isinstance(req, ResourceRequirement):
        if (
            req.resource.short_name == resource
            and req.amount == 1
            and not req.negate
            and isinstance(req.resource, ItemResourceInfo)
        ):
            return True
        return False
    if isinstance(req, RequirementArrayBase):
        return any(_does_requirement_contain_resource(subreq, resource) for subreq in req.items)
    return False


def check_for_items_to_be_replaced_by_templates(
    game: GameDescription, items_to_templates: dict[str, str]
) -> Iterator[str]:
    """
    Checks the logic database for item resources which shouldn't be used in non-template requirements and suggests
    template alternatives instead.
    Note that it will only check for item requirements which have an amount of 1.
    This allows you to use ammo or 0/negative requirements without getting caught by this check.
    :param game: A GameDescription of the game to check for.
    :param items_to_templates: A dictionary with the item shortname as the key and a recommended template name as the
    value. Note that the template does not need to exist, thus allowing you to specify it
    like this: "Can Jump High or Can Jump Very High"
    :return: Error messages of requirements which don't pass the check.
    """
    context = _create_node_context(game)

    for source_node in game.region_list.iterate_nodes():
        try:
            for destination_node, req in game.region_list.potential_nodes_from(source_node, context):
                for resource, template in items_to_templates.items():
                    if _does_requirement_contain_resource(req, resource):
                        yield (
                            f"{source_node.identifier.as_string} -> {destination_node.identifier.as_string} is using "
                            f'the resource "{resource}" directly than using the template "{template}".'
                        )
        except KeyError:
            # Broken docks
            continue


def check_for_resources_to_use_together(
    game: GameDescription, combined_resources: Mapping[str, tuple[str, ...]]
) -> Iterator[str]:
    """
    Checks the logic database for resources that should always be used together with other resources.
    :param game: A GameDescription of the game to check for.
    :param combined_resources: A dictionary with a resource shortname as the key and a tuple of
    resource shortnames which must be present in all requirements where the key-resource is present.
    The resources can be general resources and can also be mixed together. They do not need to be all ItemResources.
    For example: { HoverWithBombsTrick: (BombItem, ExplosiveDamage)}
    :return: Error messages of requirements which don't pass the check.
    """
    context = _create_node_context(game)
    requirement_cache: dict[Requirement, RequirementSet] = {}

    for source_node in game.region_list.iterate_nodes():
        try:
            for destination_node, req in game.region_list.potential_nodes_from(source_node, context):
                for resource_key, resource_value in combined_resources.items():
                    if _needed_resources_partly_satisfied(
                        req, (resource_key, resource_value), context, requirement_cache
                    ):
                        yield (
                            f"{source_node.identifier.as_string} -> {destination_node.identifier.as_string} contains "
                            f'"{resource_key}" but not "{resource_value}"'
                        )
        except KeyError:
            # Broken docks
            continue


def find_incompatible_video_links(game: GameDescription) -> Iterator[str]:
    for region in game.region_list.regions:
        for area in region.areas:
            for node in area.nodes:
                for target, requirement in area.connections.get(node, {}).items():
                    yield from get_videos(requirement, node, target)


def get_videos(req: Requirement, node: Node, target: Node) -> Iterator[str]:
    if isinstance(req, RequirementArrayBase):
        if req.comment is not None:
            for word in req.comment.split(" "):
                if "youtu" not in word:
                    continue
                if "&list" in word:
                    yield f"YouTube Playlist linked in {node.identifier.as_string} -> {target.name}."
        for i in req.items:
            yield from get_videos(i, node, target)


def check_for_redundant_hint_features(area: Area, node: PickupNode) -> Iterator[str]:
    """
    If a hint feature is present on an Area, all of its child pickups
    are treated as if they have that feature. Explicitly including
    them on the pickup is redundant.
    """
    for feature in sorted(node.hint_features):
        if feature in area.hint_features:
            yield f"{node.name} shares the hint feature '{feature.long_name}' with the area it's in."


def check_for_unnormalized_hint_features(area: Area) -> Iterator[str]:
    """
    If all pickups in an Area share the same hint feature, that feature
    should be included on the Area instead of the pickups.
    """
    pickups = [node for node in area.nodes if isinstance(node, PickupNode)]
    if not pickups:
        return
    features = pickups[0].hint_features
    for pickup in pickups:
        features &= pickup.hint_features
    for feature in sorted(features):
        yield (
            f"{area.name}'s pickups all share the hint feature '{feature.long_name}'. "
            "Add feature to the area and remove from the pickups."
        )


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
    result.extend(game.game.data.logic_db_integrity(game))
    result.extend(find_incompatible_video_links(game))

    return result
