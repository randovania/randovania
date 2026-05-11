from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container

    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


def _get_reach_class() -> type[GeneratorReach]:
    from randovania.generator.old_generator_reach import OldGeneratorReach

    return OldGeneratorReach


def _action_has_no_dangerous_resources(
    node: WorldGraphNode,
    dangerous_resources: Container[ResourceInfo],
    resources: ResourceCollection,
) -> bool:
    return all(resource not in dangerous_resources for resource, _ in node.resource_gain_on_collect(resources))


def get_collectable_resource_nodes_of_reach(
    reach: GeneratorReach,
    use_safe_nodes: bool = False,
    include_with_dangerous_resources: bool = True,
    must_be_reachable: bool = True,
) -> list[WorldGraphNode]:
    resources = reach.state.resources
    health = reach.state.health_for_damage_requirements
    dangerous_resources = reach.graph.dangerous_resources

    result = []

    node_list = reach.safe_nodes if use_safe_nodes else (reach.connected_nodes if must_be_reachable else reach.nodes)

    for node in node_list:
        if (
            not node.has_all_resources(resources)
            and node.requirement_to_collect.satisfied(resources, health)
            and (
                include_with_dangerous_resources
                or (_action_has_no_dangerous_resources(node, dangerous_resources, resources))
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
            if not action.has_all_resources(reach.state.resources):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(
    graph: WorldGraph, initial_state: State, filler_config: FillerConfiguration
) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param graph:
    :param initial_state:
    :param filler_config:
    :return:
    """
    reach = _get_reach_class().reach_from_state(graph, initial_state, filler_config)
    collect_all_safe_resources_in_reach(reach)
    return reach


def _is_new_node_state_no_worse(
    new_reach: GeneratorReach,
    old_safe_node_sets: list[set[int]],
    new_reachable_nodes: set[int],
    old_reachable_node_sets: list[set[int]],
) -> bool:
    """Utility function to check the state after one or more actions, to see if the new state isn't missing any nodes as
     either safe or reachable that was safe or reachable, respectively, at an earlier stage of the evaluation.
    :param new_reach:
    :param old_safe_node_sets:
    :param new_reachable_nodes:
    :param old_reachable_node_sets:
    :return:
    """
    for old_safe_nodes in old_safe_node_sets:
        if not old_safe_nodes <= new_reach.safe_nodes_index_set:
            return False
    for old_reachable_nodes in old_reachable_node_sets:
        if not old_reachable_nodes <= new_reachable_nodes:
            return False
    return True


def _check_if_action_was_safe(
    graph: WorldGraph,
    initial_state: State,
    action: WorldGraphNode,
    new_reach: GeneratorReach,
    new_reachable_nodes: set[int],
    previous_safe_node_sets: list[set[int]],
    old_reachable_node_sets: list[set[int]],
) -> bool:
    """
    Utility function to check if an action is safe or not. The new action is either the first or the second possibly
     unsafe action taken from the initial state. The action is considered safe if all the nodes that were reachable in
      the initial state are still reachable in the new state. Similarly, nodes that were safe in the initial state, are
       also safe after the action. If we are evaluating the second action, then additionally, any nodes that were
        reachable or safe after the first action, still has to be reachable or safe, respectively, after this second
         action.
    :param graph:
    :param initial_state:
    :param action:
    :param new_reach:
    :param new_reachable_nodes:
    :param previous_safe_node_sets:
    :param old_reachable_node_sets:
    :return:
    """
    if _is_new_node_state_no_worse(new_reach, previous_safe_node_sets, new_reachable_nodes, old_reachable_node_sets):
        if _action_has_no_dangerous_resources(action, graph.dangerous_resources, initial_state.resources):
            return True

        # It'll only be reachable in the new state if it already is in the existing state
        # And since we already calculated the reachable nodes for this reach, this is a cheap operation!
        if new_reach.is_reachable_node(initial_state.node):
            # In this case, the action provides a dangerous resource but collecting it still lets us go back
            # to where we started and the set of safe nodes didn't shrink
            # We'll now create an entire new GeneratorReach and check if the safe nodes really didn't shrink.

            return True
    return False


def _recalculate_reach_after_action(
    previous_reach: GeneratorReach, action: WorldGraphNode, graph: WorldGraph
) -> GeneratorReach:
    """
    Create a new GeneratorReach that after collecting the given possibly unsafe action. Afterward, collect all safe
     resources. Finally, the returned reach is rebuild from state, using the graph, which is necessary for some edge
      cases related to dangerous actions.
    :param previous_reach:
    :param action:
    :param graph:
    :return:
    """
    next_reach = copy.deepcopy(previous_reach)
    next_reach.act_on(action)
    collect_all_safe_resources_in_reach(next_reach)

    experimental_reach = _get_reach_class().reach_from_state(
        graph, next_reach.state.copy(), previous_reach.filler_config
    )

    return experimental_reach


def advance_after_action(previous_reach: GeneratorReach) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :return:
    """
    graph = previous_reach.graph
    collect_all_safe_resources_in_reach(previous_reach)
    initial_state = previous_reach.state

    previous_safe_nodes = previous_reach.safe_nodes_index_set
    old_reachable_nodes = previous_reach.set_of_reachable_node_indices()

    for action in get_collectable_resource_nodes_of_reach(previous_reach):
        # print("Trying to collect {} and it's not dangerous. Copying...".format(action.full_name()))
        next_reach = _recalculate_reach_after_action(previous_reach, action, graph)
        middle_safe_nodes = next_reach.safe_nodes_index_set
        middle_reachable_nodes = next_reach.set_of_reachable_node_indices()

        if _check_if_action_was_safe(
            graph,
            initial_state,
            action,
            next_reach,
            middle_reachable_nodes,
            previous_safe_node_sets=[previous_safe_nodes],
            old_reachable_node_sets=[old_reachable_nodes],
        ):
            return advance_after_action(next_reach)

        for next_action in get_collectable_resource_nodes_of_reach(next_reach):
            # This loop is largely the same logic as above, and exists for the purpose of trying a second possibly
            # unsafe action to get an even deeper evaluation of new safe resources.

            next_next_reach = _recalculate_reach_after_action(next_reach, next_action, graph)

            last_reachable_nodes = next_next_reach.set_of_reachable_node_indices()

            if _check_if_action_was_safe(
                graph,
                initial_state,
                next_action,
                next_next_reach,
                last_reachable_nodes,
                previous_safe_node_sets=[previous_safe_nodes, middle_safe_nodes],
                old_reachable_node_sets=[old_reachable_nodes, middle_reachable_nodes],
            ):
                return advance_after_action(next_next_reach)

    # We couldn't improve this reach, so just return it
    return previous_reach
