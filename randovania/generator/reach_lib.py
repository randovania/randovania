from __future__ import annotations

import copy
import typing
from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.game_description import GameDescription
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.resolver.state import State

    NodeT = typing.TypeVar("NodeT", bound=Node)
    ResourceNodeT = typing.TypeVar("ResourceNodeT", bound=ResourceNode)


def _filter_resource_nodes(nodes: Iterator[Node]) -> Iterator[ResourceNode]:
    for node in nodes:
        if node.is_resource_node:
            yield typing.cast("ResourceNode", node)


def filter_pickup_nodes(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            yield node


def _filter_collectable(resource_nodes: Iterator[ResourceNodeT], reach: GeneratorReach) -> Iterator[ResourceNodeT]:
    context = reach.node_context()
    for resource_node in resource_nodes:
        if resource_node.should_collect(context) and resource_node.requirement_to_collect().satisfied(
            context, reach.state.health_for_damage_requirements
        ):
            yield resource_node


def _filter_reachable(nodes: Iterator[NodeT], reach: GeneratorReach) -> Iterator[NodeT]:
    for node in nodes:
        if reach.is_reachable_node(node):
            yield node


def _filter_out_dangerous_actions(
    resource_nodes: Iterator[ResourceNodeT],
    game: GameDescription,
    context: NodeContext,
) -> Iterator[ResourceNodeT]:
    for resource_node in resource_nodes:
        if all(
            resource not in game.dangerous_resources for resource, _ in resource_node.resource_gain_on_collect(context)
        ):
            yield resource_node


def _get_safe_resources(reach: GeneratorReach) -> Iterator[ResourceNode]:
    yield from _filter_reachable(
        _filter_out_dangerous_actions(
            collectable_resource_nodes(reach.safe_nodes, reach), reach.game, reach.node_context()
        ),
        reach,
    )


def collectable_resource_nodes(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[ResourceNode]:
    return _filter_collectable(_filter_resource_nodes(nodes), reach)


def get_collectable_resource_nodes_of_reach(reach: GeneratorReach) -> list[ResourceNode]:
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


def reach_with_all_safe_resources(
    game: GameDescription, initial_state: State, filler_config: FillerConfiguration
) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param game:
    :param initial_state:
    :return:
    """
    from randovania.generator.old_generator_reach import OldGeneratorReach as GR

    # from randovania.generator.trust_generator_reach import TrustGeneratorReach as GR
    reach = GR.reach_from_state(game, initial_state, filler_config)
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

    previous_safe_nodes = set(previous_reach.safe_nodes)

    for action in get_collectable_resource_nodes_of_reach(previous_reach):
        # print("Trying to collect {} and it's not dangerous. Copying...".format(action.name))
        next_reach = copy.deepcopy(previous_reach)
        next_reach.act_on(action)
        collect_all_safe_resources_in_reach(next_reach)

        if previous_safe_nodes <= set(next_reach.safe_nodes):
            # print("Non-safe {} was good".format(logic.game.node_name(action)))
            return advance_reach_with_possible_unsafe_resources(next_reach)

        if next_reach.is_reachable_node(initial_state.node):
            next_next_state = next_reach.state.copy()
            next_next_state.node = initial_state.node

            next_reach = reach_with_all_safe_resources(game, next_next_state, previous_reach.filler_config)
            if previous_safe_nodes <= set(next_reach.safe_nodes):
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

    if potential_reach.filler_config.consider_possible_unsafe_resources:
        return advance_reach_with_possible_unsafe_resources(potential_reach)

    else:
        collect_all_safe_resources_in_reach(potential_reach)
        return potential_reach
