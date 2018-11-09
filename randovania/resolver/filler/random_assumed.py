import copy
from random import Random
from typing import Tuple, Iterator

from randovania.game_description.node import Node, PickupNode
from randovania.game_description.resources import PickupEntry
from randovania.resolver import debug
from randovania.resolver.game_patches import GamePatches, PickupAssignment
from randovania.resolver.generator import _filter_unassigned_pickup_nodes
from randovania.resolver.generator_reach import advance_reach_with_possible_unsafe_resources, \
    reach_with_all_safe_resources, collect_all_safe_resources_in_reach, filter_reachable, pickup_nodes_that_can_reach
from randovania.resolver.logic import Logic
from randovania.resolver.random_lib import iterate_with_weights
from randovania.resolver.state import State, add_resource_gain_to_state, state_with_pickup


def _random_assumed_filler(logic: Logic,
                           initial_state: State,
                           patches: GamePatches,
                           available_pickups: Tuple[PickupEntry],
                           rng: Random,
                           ) -> PickupAssignment:
    pickup_assignment = copy.copy(patches.pickup_assignment)
    print("Major items: {}".format([item.item for item in available_pickups]))

    base_reach = advance_reach_with_possible_unsafe_resources(
        reach_with_all_safe_resources(logic, initial_state, patches),
        patches)

    reaches_for_pickup = {}

    previous_reach = base_reach
    for pickup in reversed(available_pickups):
        print("** Preparing reach for {}".format(pickup.item))
        new_reach = copy.deepcopy(previous_reach)
        add_resource_gain_to_state(new_reach.state, pickup.resource_gain())
        new_reach.state.previous_state = new_reach.state
        new_reach.advance_to(new_reach.state)
        collect_all_safe_resources_in_reach(new_reach, patches)
        previous_reach = advance_reach_with_possible_unsafe_resources(new_reach, patches)
        reaches_for_pickup[pickup] = previous_reach

    for i, pickup in enumerate(available_pickups):
        print("\n\n\nWill place {}, have {} pickups left".format(pickup, len(available_pickups) - i - 1))
        reach = reaches_for_pickup[pickup]
        debug.print_actions_of_reach(reach)
        escape_state = state_with_pickup(reach.state, pickup)

        total_pickup_nodes = list(_filter_pickups(filter_reachable(reach.nodes, reach)))
        pickup_nodes = list(_filter_unassigned_pickup_nodes(total_pickup_nodes, pickup_assignment))
        num_nodes = len(pickup_nodes)
        actions_weights = {
            node: len(path)
            for node, path in reach.shortest_path_from(initial_state.node).items()
        }

        try:
            pickup_node = next(pickup_nodes_that_can_reach(iterate_with_weights(pickup_nodes, actions_weights, rng),
                                                           reach_with_all_safe_resources(logic, escape_state, patches),
                                                           set(reach.safe_nodes)))
            print("Placed {} at {}. Had {} available of {} nodes.".format(pickup.item,
                                                                          logic.game.node_name(pickup_node, True),
                                                                          num_nodes,
                                                                          len(total_pickup_nodes)))

        except StopIteration:
            print("\n".join(logic.game.node_name(node, True) for node in reach.safe_nodes))
            raise Exception("Couldn't place {}. Had {} available of {} nodes.".format(pickup.item,
                                                                                      num_nodes,
                                                                                      len(total_pickup_nodes)
                                                                                      ))

        pickup_assignment[pickup_node.pickup_index] = pickup

    return pickup_assignment


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)
