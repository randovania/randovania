import copy
from typing import Iterator, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.world.node import Node, ResourceNode, PickupNode
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver.state import State


def _filter_resource_nodes(nodes: Iterator[Node]) -> Iterator[ResourceNode]:
    for node in nodes:
        if node.is_resource_node:
            yield node


def filter_pickup_nodes(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            yield node


def _filter_collectable(resource_nodes: Iterator[ResourceNode], reach: GeneratorReach) -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if resource_node.can_collect(reach.state.patches, reach.state.resources, reach.all_nodes,
                                     reach.state.resource_database):
            yield resource_node


def _filter_reachable(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[Node]:
    for node in nodes:
        if reach.is_reachable_node(node):
            yield node


def _filter_out_dangerous_actions(resource_nodes: Iterator[ResourceNode],
                                  game: GameDescription,
                                  ) -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if resource_node.resource() not in game.dangerous_resources:
            yield resource_node


def _get_safe_resources(reach: GeneratorReach) -> Iterator[ResourceNode]:
    yield from _filter_reachable(
        _filter_out_dangerous_actions(
            collectable_resource_nodes(reach.safe_nodes, reach),
            reach.game),
        reach
    )


def collectable_resource_nodes(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[ResourceNode]:
    return _filter_collectable(_filter_resource_nodes(nodes), reach)


def get_collectable_resource_nodes_of_reach(reach: GeneratorReach) -> List[ResourceNode]:
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
            if action.can_collect(reach.state.patches, reach.state.resources, reach.all_nodes,
                                  reach.state.resource_database):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(game: GameDescription, initial_state: State) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param game:
    :param initial_state:
    :return:
    """
    from randovania.generator.old_generator_reach import OldGeneratorReach as GR
    # from randovania.generator.trust_generator_reach import TrustGeneratorReach as GR
    reach = GR.reach_from_state(game, initial_state)
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

            next_reach = reach_with_all_safe_resources(game, next_next_state)
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
    collect_all_safe_resources_in_reach(potential_reach)
    return potential_reach
    # return advance_reach_with_possible_unsafe_resources(potential_reach)
