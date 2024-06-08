from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode

    NodeT = typing.TypeVar("NodeT", bound=Node)
    ResourceNodeT = typing.TypeVar("ResourceNodeT", bound=ResourceNode)


def _filter_resource_nodes(nodes: Iterator[WorldGraphNode]) -> Iterator[WorldGraphNode]:
    for node in nodes:
        if node.is_resource_node():
            yield node


def filter_pickup_nodes(nodes: Iterator[WorldGraphNode]) -> Iterator[WorldGraphNode]:
    for node in nodes:
        if node.pickup_index is not None:
            yield node


def _filter_reachable(nodes: Iterator[WorldGraphNode], reach: GeneratorReach) -> Iterator[WorldGraphNode]:
    for node in nodes:
        if reach.is_reachable_node(node):
            yield node


def _is_collectable_node(node: WorldGraphNode, context: NodeContext, reach: GeneratorReach) -> bool:
    return (
        node.is_resource_node()
        and node.should_collect(context)
        and node.requirement_to_collect.satisfied(context, reach.state.energy)
    )


def _get_safe_resources(reach: GeneratorReach) -> Iterator[WorldGraphNode]:
    context = reach.node_context()
    dangerous_resources = reach.world_graph.dangerous_resources

    for node in reach.safe_nodes:
        if _is_collectable_node(node, context, reach):
            if all(resource not in dangerous_resources for resource, _ in node.resource_gain_on_collect(context)):
                if reach.is_reachable_node(node):
                    yield node


def collectable_resource_nodes(nodes: Iterator[WorldGraphNode], reach: GeneratorReach) -> Iterator[WorldGraphNode]:
    context = reach.node_context()
    for node in nodes:
        if _is_collectable_node(node, context, reach):
            yield node


def get_collectable_resource_nodes_of_reach(reach: GeneratorReach) -> list[WorldGraphNode]:
    return list(collectable_resource_nodes(_filter_reachable(reach.nodes, reach), reach))


def collect_all_safe_resources_in_reach(reach: GeneratorReach) -> None:
    """

    :param reach:
    :return:
    """
    while True:
        actions = list(_get_safe_resources(reach))
        if not actions:
            break

        for action in actions:
            # requirement_to_collect was checked in `_get_safe_resources`, so we're assuming it's already satisfied
            if action.should_collect(reach.node_context()):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(graph: WorldGraph, initial_state: State) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param graph:
    :param initial_state:
    :return:
    """
    from randovania.generator.old_generator_reach import OldGeneratorReach as GR

    # from randovania.generator.trust_generator_reach import TrustGeneratorReach as GR
    reach = GR.reach_from_state(graph, initial_state)
    collect_all_safe_resources_in_reach(reach)
    return reach


def advance_reach_with_possible_unsafe_resources(previous_reach: GeneratorReach) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :return:
    """

    game = previous_reach.game
    collect_all_safe_resources_in_reach(previous_reach)
    initial_state = previous_reach.state

    previous_safe_nodes = previous_reach.safe_node_indices_set()

    for action in get_collectable_resource_nodes_of_reach(previous_reach):
        # print("Trying to collect {} and it's not dangerous. Copying...".format(action.name))
        next_reach = copy.deepcopy(previous_reach)
        next_reach.act_on(action)
        collect_all_safe_resources_in_reach(next_reach)

        if previous_safe_nodes <= next_reach.safe_node_indices_set():
            # print("Non-safe {} was good".format(logic.game.node_name(action)))
            return advance_reach_with_possible_unsafe_resources(next_reach)

        if next_reach.is_reachable_node(initial_state.node):
            next_next_state = next_reach.state.copy()
            next_next_state.node = initial_state.node

            next_reach = reach_with_all_safe_resources(game, next_next_state)
            if previous_safe_nodes <= next_reach.safe_node_indices_set():
                # print("Non-safe {} could reach back to where we were".format(logic.game.node_name(action)))
                return advance_reach_with_possible_unsafe_resources(next_reach)
        else:
            pass

    # We couldn't improve this reach, so just return it
    return previous_reach


def advance_to_with_reach_copy(base_reach: GeneratorReach, state: State) -> GeneratorReach:
    """
    Copies the given Reach, advances to the given State and collect all possible resources.
    :param base_reach:
    :param state:
    :return:
    """
    potential_reach = copy.deepcopy(base_reach)
    potential_reach.advance_to(state)
    collect_all_safe_resources_in_reach(potential_reach)
    return potential_reach
    # return advance_reach_with_possible_unsafe_resources(potential_reach)
