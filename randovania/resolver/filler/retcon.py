import collections
import itertools
from random import Random
from typing import Tuple, Iterator, NamedTuple, Set, Union, Dict, FrozenSet, Callable, List

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode, PickupNode, Node
from randovania.game_description.requirements import RequirementList
from randovania.game_description.resources import PickupEntry, PickupIndex, PickupAssignment, ResourceGain, \
    ResourceInfo, CurrentResources
from randovania.resolver import debug
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
    def from_reach(cls, reach: GeneratorReach) -> "UncollectedState":
        return UncollectedState(
            set(_filter_unassigned_pickup_indices(reach.state.collected_pickup_indices,
                                                  reach.state.patches.pickup_assignment)),
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
                                     ) -> GeneratorReach:
    return advance_to_with_reach_copy(reach, state_with_pickup(reach.state, progression))


Action = Union[ResourceNode, PickupEntry]


def _resources_in_pickup(pickup: PickupEntry, current_resources: CurrentResources) -> FrozenSet[ResourceInfo]:
    resource_gain = pickup.resource_gain(current_resources)
    return frozenset(resource for resource, _ in resource_gain)


def retcon_playthrough_filler(logic: Logic,
                              initial_state: State,
                              pickups_left: List[PickupEntry],
                              rng: Random,
                              status_update: Callable[[str], None],
                              ) -> GamePatches:
    debug.debug_print("Major items: {}".format([item.name for item in pickups_left]))
    last_message = "Starting."

    reach = advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(logic, initial_state))

    pickup_index_seen_count: Dict[PickupIndex, int] = collections.defaultdict(int)

    while pickups_left:
        current_uncollected = UncollectedState.from_reach(reach)

        progression_pickups = _calculate_progression_pickups(pickups_left, reach)
        print_retcon_loop_start(current_uncollected, logic, pickups_left, reach)

        for pickup_index in reach.state.collected_pickup_indices:
            pickup_index_seen_count[pickup_index] += 1
        print_new_pickup_indices(logic, reach, pickup_index_seen_count)

        def action_report(message: str):
            status_update("{} {}".format(last_message, message))

        actions_weights = _calculate_potential_actions(reach, progression_pickups,
                                                       current_uncollected, action_report)

        try:
            action = next(iterate_with_weights(list(actions_weights.keys()), actions_weights, rng))
        except StopIteration:
            if actions_weights:
                action = rng.choice(list(actions_weights.keys()))
            else:
                raise RuntimeError("Unable to generate, no actions found after placing {} items.".format(
                    len(reach.state.patches.pickup_assignment)))

        if isinstance(action, PickupEntry):
            assert action in pickups_left

            pickup_index_weight = {
                pickup_index: 1 / (min(pickup_index_seen_count[pickup_index], 10) ** 2)
                for pickup_index in current_uncollected.indices
            }
            assert pickup_index_weight, "Pickups should only be added to the actions dict " \
                                        "when there are unassigned pickups"

            # print(">>>>>>>>>>>>>")
            # world_list = logic.game.world_list
            # for pickup_index in sorted(current_uncollected.indices, key=lambda x: pickup_index_weight[x]):
            #     print("{1:.6f} {2:5}: {0}".format(
            #         world_list.node_name(find_pickup_node_with_index(pickup_index, world_list.all_nodes)),
            #         pickup_index_weight[pickup_index],
            #         pickup_index_seen_count[pickup_index]))

            pickup_index = next(iterate_with_weights(list(current_uncollected.indices), pickup_index_weight, rng))

            # TODO: this item is potentially dangerous and we should remove the invalidated paths
            next_state = reach.state.assign_pickup_to_index(pickup_index, action)
            pickups_left.remove(action)

            last_message = "Placed {} items so far, {} left.".format(
                len(next_state.patches.pickup_assignment), len(pickups_left) - 1)
            status_update(last_message)
            print_retcon_place_pickup(action, logic, pickup_index)

            reach.advance_to(next_state)

        else:
            last_message = "Triggered an event out of {} options.".format(len(actions_weights))
            status_update(last_message)
            debug_print_collect_event(action, logic)
            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            reach.act_on(action)

        reach = advance_reach_with_possible_unsafe_resources(reach)

        if logic.game.victory_condition.satisfied(reach.state.resources, reach.state.resource_database):
            debug.debug_print("Finished because we can win")
            break

    if not pickups_left:
        debug.debug_print("Finished because we have nothing else to distribute")

    return reach.state.patches


def _calculate_progression_pickups(pickups_left: Iterator[PickupEntry],
                                   reach: GeneratorReach,
                                   ) -> Tuple[PickupEntry, ...]:
    satisfiable_requirements: FrozenSet[RequirementList] = frozenset(itertools.chain.from_iterable(
        requirements.alternatives
        for requirements in reach.unreachable_nodes_with_requirements().values()
    ))
    interesting_resources = calculate_interesting_resources(
        satisfiable_requirements,
        reach.state.resources,
        reach.state.resource_database
    )

    progression_pickups = []

    for pickup in pickups_left:
        if pickup in progression_pickups:
            continue
        if _resources_in_pickup(pickup, reach.state.resources).intersection(interesting_resources):
            progression_pickups.append(pickup)

    return tuple(progression_pickups)


def _calculate_weights_for(potential_reach: GeneratorReach,
                           current_uncollected: UncollectedState,
                           name: str
                           ) -> float:
    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
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

    return weight


def _calculate_potential_actions(reach: GeneratorReach,
                                 progression_pickups: Tuple[PickupEntry, ...],
                                 current_uncollected: UncollectedState,
                                 status_update: Callable[[str], None]):
    actions_weights: Dict[Action, float] = {}
    uncollected_resource_nodes = get_uncollected_resource_nodes_of_reach(reach)
    total_options = len(uncollected_resource_nodes)
    options_considered = 0

    def update_for_option():
        nonlocal options_considered
        options_considered += 1
        status_update("Checked {} of {} options.".format(options_considered, total_options))

    if current_uncollected.indices:
        total_options += len(progression_pickups)
        for progression in progression_pickups:
            actions_weights[progression] = _calculate_weights_for(_calculate_reach_for_progression(reach,
                                                                                                   progression),
                                                                  current_uncollected,
                                                                  progression.name) + progression.probability_offset
            update_for_option()

    for resource in uncollected_resource_nodes:
        actions_weights[resource] = _calculate_weights_for(
            advance_to_with_reach_copy(reach, reach.state.act_on_node(resource)),
            current_uncollected,
            resource.name)
        update_for_option()

    if debug.debug_level() > 1:
        for action, weight in actions_weights.items():
            print("{} - {}".format(action.name, weight))

    return actions_weights


def debug_print_collect_event(action, logic):
    if debug.debug_level() > 0:
        print("\n--> Collecting {}".format(logic.game.world_list.node_name(action, with_world=True)))


def print_retcon_loop_start(current_uncollected: UncollectedState,
                            logic: Logic,
                            pickups_left: Iterator[PickupEntry],
                            reach: GeneratorReach,
                            ):
    if debug.debug_level() > 0:
        if debug.debug_level() > 1:
            extra = ", pickups_left: {}".format([pickup.name for pickup in pickups_left])
        else:
            extra = ""

        print("\n\n===============================")
        print("\n>>> From {}, {} open pickup indices, {} open resources{}".format(
            logic.game.world_list.node_name(reach.state.node, with_world=True),
            len(current_uncollected.indices),
            len(current_uncollected.resources),
            extra
        ))


def print_retcon_place_pickup(action: PickupEntry, logic: Logic, pickup_index: PickupIndex):
    world_list = logic.game.world_list
    if debug.debug_level() > 0:
        print("\n--> Placing {} at {}".format(
            action.name,
            world_list.node_name(find_pickup_node_with_index(pickup_index, world_list.all_nodes), with_world=True)))


def print_new_pickup_indices(logic: Logic,
                             reach: GeneratorReach,
                             pickup_index_seen_count: Dict[PickupIndex, int],
                             ):
    world_list = logic.game.world_list
    if debug.debug_level() > 0:
        for index, count in pickup_index_seen_count.items():
            if count == 1:
                node = find_pickup_node_with_index(index, world_list.all_nodes)
                print("-> New Pickup Node: {}".format(
                    world_list.node_name(node,
                                         with_world=True)))
                if debug.debug_level() > 1:
                    paths = reach.shortest_path_from(node)
                    path = paths.get(reach.state.node, [])
                    print([node.name for node in path])
        print("")


def _filter_unassigned_pickup_indices(indices: Iterator[PickupIndex],
                                      pickup_assignment: PickupAssignment,
                                      ) -> Iterator[PickupIndex]:
    for index in indices:
        if index not in pickup_assignment:
            yield index
