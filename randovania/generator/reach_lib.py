from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container, Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import GraphOrResourceNode, State
    from randovania.graph.world_graph import WorldGraph


def _get_reach_class() -> type[GeneratorReach]:
    from randovania.generator.old_generator_reach import OldGeneratorReach

    return OldGeneratorReach


def _action_has_no_dangerous_resources(
    node: GraphOrResourceNode,
    dangerous_resources: Container[ResourceInfo],
    context: NodeContext,
) -> bool:
    return all(resource not in dangerous_resources for resource, _ in node.resource_gain_on_collect(context))


def get_collectable_resource_nodes_of_reach(
    reach: GeneratorReach,
    use_safe_nodes: bool = False,
    include_with_dangerous_resources: bool = True,
    must_be_reachable: bool = True,
) -> list[GraphOrResourceNode]:
    context = reach.node_context()
    health = reach.state.health_for_damage_requirements
    dangerous_resources = reach.game.dangerous_resources

    result = []

    node_list = typing.cast("Iterator[GraphOrResourceNode]", reach.safe_nodes if use_safe_nodes else reach.nodes)

    for node in node_list:
        if (
            node.is_resource_node()
            and node.should_collect(context)
            and node.requirement_to_collect.satisfied(context, health)
            and (
                include_with_dangerous_resources
                or (_action_has_no_dangerous_resources(node, dangerous_resources, context))
            )
            and (not must_be_reachable or reach.is_reachable_node(node))
        ):
            result.append(node)

    return result


def collect_all_safe_resources_in_reach(reach: GeneratorReach) -> None:
    while True:
        actions = get_collectable_resource_nodes_of_reach(
            reach,
            use_safe_nodes=True,
            include_with_dangerous_resources=False,
        )
        if not actions:
            break

        for action in actions:
            # requirement_to_collect was checked in `_get_safe_resources`, so we're assuming it's already satisfied
            if action.should_collect(reach.node_context()):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(
    game: GameDescription | WorldGraph, initial_state: State, filler_config: FillerConfiguration
) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param game:
    :param initial_state:
    :param filler_config:
    :return:
    """
    reach = _get_reach_class().reach_from_state(game, initial_state, filler_config)
    collect_all_safe_resources_in_reach(reach)
    return reach


def advance_after_action(previous_reach: GeneratorReach) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :return:
    """
    game = previous_reach.game
    collect_all_safe_resources_in_reach(previous_reach)
    initial_state = previous_reach.state

    previous_safe_nodes = previous_reach.safe_nodes_index_set

    for action in get_collectable_resource_nodes_of_reach(previous_reach):
        # print("Trying to collect {} and it's not dangerous. Copying...".format(action.full_name()))
        next_reach = copy.deepcopy(previous_reach)
        next_reach.act_on(action)
        collect_all_safe_resources_in_reach(next_reach)

        if previous_safe_nodes <= next_reach.safe_nodes_index_set:
            if _action_has_no_dangerous_resources(action, game.dangerous_resources, previous_reach.node_context()):
                # print("Non-safe {} was good".format(action.full_name()))
                return advance_after_action(next_reach)

            # It'll only be reachable in the new state if it already is in the existing state
            # And since we already calculated the reachable nodes for this reach, this is a cheap operation!
            if next_reach.is_reachable_node(initial_state.node):
                # In this case, the action provides a dangerous resource but collecting it still lets us go back
                # to where we started and the set of safe nodes didn't shrink
                # We'll now create an entire new GeneratorReach and check if the safe nodes really didn't shrink.

                # No need to call collect_all_safe_resources_in_reach on this new reach,
                # as we've already collected everything at the start of this loop
                experimental_reach = _get_reach_class().reach_from_state(
                    game, next_reach.state.copy(), previous_reach.filler_config
                )
                # assert experimental_reach.safe_nodes_index_set <= next_reach.safe_nodes_index_set

                if previous_safe_nodes <= experimental_reach.safe_nodes_index_set:
                    # print("Non-safe {} could reach back to where we were".format(action.full_name()))
                    return advance_after_action(experimental_reach)

        # print("Non-safe {} was skipped".format(action.full_name()))

    # We couldn't improve this reach, so just return it
    return previous_reach
