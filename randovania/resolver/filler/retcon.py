import collections
import copy
import itertools
from random import Random
from typing import Tuple, Iterator, NamedTuple, Set, Optional, Union, Dict, FrozenSet, Callable

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.node import ResourceNode, PickupNode, Node
from randovania.game_description.requirements import RequirementList
from randovania.game_description.resources import PickupEntry, PickupIndex
from randovania.resolver import debug
from randovania.resolver.game_patches import GamePatches, PickupAssignment
from randovania.resolver.generator_reach import GeneratorReach, uncollected_resources, \
    advance_reach_with_possible_unsafe_resources, reach_with_all_safe_resources, \
    get_uncollected_resource_nodes_of_reach, advance_to_with_reach_copy
from randovania.resolver.logic import Logic
from randovania.resolver.random_lib import iterate_with_weights
from randovania.resolver.state import State, state_with_pickup


class UncollectedState(NamedTuple):
    indices: Set[PickupIndex]
    resources: Set[ResourceNode]

    @classmethod
    def from_reach(cls,
                   reach: GeneratorReach,
                   pickup_assignment: PickupAssignment,
                   ) -> "UncollectedState":
        return UncollectedState(
            set(_filter_unassigned_pickup_indices(reach.state.collected_pickup_indices,
                                                  pickup_assignment)),
            set(uncollected_resources(reach.connected_nodes, reach))
        )

    def __sub__(self, other: "UncollectedState") -> "UncollectedState":
        return UncollectedState(
            self.indices - other.indices,
            self.resources - other.resources
        )


def find_pickup_node_with_index(index: PickupIndex,
                                haystack: Iterator[Node],
                                ) -> PickupNode:
    for node in haystack:
        if isinstance(node, PickupNode) and node.pickup_index == index:
            return node


def _calculate_reach_for_progression(reach: GeneratorReach,
                                     progression: PickupEntry,
                                     reach_for_pickup: Dict[PickupEntry, GeneratorReach],
                                     ):

    return advance_to_with_reach_copy(reach,
                                      state_with_pickup(reach.state, progression),
                                      reach.logic.patches)


def _calculate_weights_for(potential_reach: GeneratorReach,
                           pickup_assignment: PickupAssignment,
                           current_uncollected: UncollectedState,
                           name: str
                           ) -> Optional[Tuple[GeneratorReach, float]]:
    potential_uncollected = UncollectedState.from_reach(potential_reach, pickup_assignment) - current_uncollected
    weight = len(potential_uncollected.resources) + len(potential_uncollected.indices)

    # def _path(node):
    #     return str([
    #         reach.logic.game.node_name(node) for node in potential_reach._reachable_paths[node]
    #     ])
    #
    # messages = [
    #     reach.logic.game.node_name(node) + ": " + _path(node)
    #     for node in potential_uncollected.resources
    # ]
    # for index in _filter_unassigned_pickup_indices(potential_reach.state.collected_pickup_indices,
    #                                                pickup_assignment):
    #     if reach.state.has_resource(index):
    #         continue
    #     for node in potential_reach.nodes:
    #         if isinstance(node, PickupNode) and node.pickup_index == index:
    #             messages.append("Collected Pickup Node: {}".format(reach.logic.game.node_name(node)))
    #
    # if messages:
    #     messages = "\n* " + "\n* ".join(messages)
    # else:
    #     messages = ""

    if debug._DEBUG_LEVEL > 1:
        print("{} - {}".format(name, weight))

    if weight > 0:
        return potential_reach, weight


Action = Union[ResourceNode, PickupEntry]


def retcon_playthrough_filler(logic: Logic,
                              initial_state: State,
                              patches: GamePatches,
                              available_pickups: Tuple[PickupEntry],
                              rng: Random,
                              status_update: Callable[[str], None],
                              ) -> PickupAssignment:
    pickup_assignment = copy.copy(patches.pickup_assignment)
    print("Major items: {}".format([item.item for item in available_pickups]))
    last_message = "Starting."

    reach = advance_reach_with_possible_unsafe_resources(
        reach_with_all_safe_resources(logic, initial_state, patches),
        patches)

    pickup_index_seen_count: Dict[PickupIndex, int] = collections.defaultdict(int)
    reach_for_pickup: Dict[PickupEntry, GeneratorReach] = {}

    while True:
        current_uncollected = UncollectedState.from_reach(reach, pickup_assignment)

        reach_for_action: Dict[Action, GeneratorReach] = {}
        actions_weights: Dict[Action, float] = {}

        pickups_left = {
            pickup.name: pickup
            for pickup in available_pickups if pickup not in pickup_assignment.values()
        }

        if not pickups_left:
            print("Finished because we have nothing else to distribute")
            break

        satisfiable_requirements: FrozenSet[RequirementList] = frozenset(itertools.chain.from_iterable(
            requirements.alternatives
            for requirements in reach.unreachable_nodes_with_requirements().values()
        ))
        interesting_resources = calculate_interesting_resources(
            satisfiable_requirements,
            reach.state.resources,
            reach.state.resource_database
        )
        progression_pickups = [
            pickup
            for pickup in pickups_left.values()
            if set(pickup.resources.keys()).intersection(interesting_resources)
        ]

        print_retcon_loop_start(current_uncollected, logic, pickups_left, reach)

        for pickup_index in reach.state.collected_pickup_indices:
            pickup_index_seen_count[pickup_index] += 1

        uncollected_resource_nodes = get_uncollected_resource_nodes_of_reach(reach)
        total_options = len(uncollected_resource_nodes)
        options_considered = 0

        def update_for_option():
            nonlocal options_considered
            options_considered += 1
            status_update("{} Checked {} of {} options.".format(last_message, options_considered, total_options))

        if current_uncollected.indices:
            total_options += len(progression_pickups)
            for progression in progression_pickups:
                potential_result = _calculate_weights_for(_calculate_reach_for_progression(reach,
                                                                                           progression,
                                                                                           reach_for_pickup),
                                                          pickup_assignment,
                                                          current_uncollected,
                                                          progression.name)
                update_for_option()
                if potential_result is not None:
                    reach_for_action[progression], actions_weights[progression] = potential_result

        for resource in uncollected_resource_nodes:

            potential_result = _calculate_weights_for(
                advance_to_with_reach_copy(reach,
                                           reach.state.act_on_node(resource, patches),
                                           reach.logic.patches),
                pickup_assignment,
                current_uncollected,
                resource.name)
            update_for_option()
            if potential_result is not None:
                reach_for_action[resource], actions_weights[resource] = potential_result
                # actions_weights[resource] *= 10

        try:
            action = next(iterate_with_weights(list(actions_weights.keys()), actions_weights, rng))
        except StopIteration:
            if progression_pickups:
                action = rng.choice(progression_pickups)
            else:
                raise RuntimeError("We have no more actions, ohno. Pickups left: {}".format(list(pickups_left.keys())))

        if isinstance(action, PickupEntry):
            next_state = state_with_pickup(reach.state, action)

            pickup_index_weight = {
                pickup_index: 1 / (pickup_index_seen_count[pickup_index] ** 2)
                for pickup_index in current_uncollected.indices
            }

            pickup_index = next(iterate_with_weights(list(current_uncollected.indices), pickup_index_weight, rng))
            pickup_assignment[pickup_index] = action

            last_message = "Placed {} items so far, {} left.".format(len(pickup_assignment), len(pickups_left) - 1)
            status_update(last_message)
            print_retcon_place_pickup(action, logic, pickup_index)

        else:
            last_message = "Triggered an event {} options.".format(options_considered)
            status_update(last_message)
            print("\n--> Collecting {}".format(logic.game.node_name(action, with_world=True)))
            next_state = reach.state.act_on_node(action, patches)

        reach.advance_to(next_state)
        reach = advance_reach_with_possible_unsafe_resources(reach, patches)

        if logic.game.victory_condition.satisfied(reach.state.resources, reach.state.resource_database):
            print("Finished because we can win")
            break

    return pickup_assignment


def print_retcon_loop_start(current_uncollected, logic, pickups_left, reach):
    if debug._DEBUG_LEVEL > 0:
        if debug._DEBUG_LEVEL > 1:
            extra = ", pickups_left: {}".format(list(pickups_left.keys()))
        else:
            extra = ""

        print("\n\n===============================")
        print("\n>>> From {}, {} open pickup indices, {} open resources{}".format(
            logic.game.node_name(reach.state.node, with_world=True),
            len(current_uncollected.indices),
            len(current_uncollected.resources),
            extra
        ))


def print_retcon_place_pickup(action, logic, pickup_index):
    if debug._DEBUG_LEVEL > 0:
        print("\n--> Placing {} at {}".format(
            action.name,
            logic.game.node_name(find_pickup_node_with_index(pickup_index, logic.game.all_nodes), with_world=True)))


def _filter_unassigned_pickup_indices(indices: Iterator[PickupIndex],
                                      pickup_assignment: PickupAssignment,
                                      ) -> Iterator[PickupIndex]:
    for index in indices:
        if index not in pickup_assignment:
            yield index
