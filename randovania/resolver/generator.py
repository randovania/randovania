import copy
import multiprocessing.dummy
from random import Random
from typing import List, Tuple, Iterator, Optional, FrozenSet, Callable, Dict, TypeVar, Iterable, Union, Set

import randovania.games.prime.claris_randomizer
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription, calculate_interesting_resources
from randovania.game_description.node import EventNode, Node, PickupNode, is_resource_node, ResourceNode
from randovania.game_description.resources import ResourceInfo, ResourceDatabase, CurrentResources, PickupEntry, \
    PickupIndex
from randovania.resolver import debug, resolver
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.game_patches import GamePatches, PickupAssignment
from randovania.resolver.generator_reach import filter_reachable, \
    reach_with_all_safe_resources, advance_reach_with_possible_unsafe_resources, pickup_nodes_that_can_reach, \
    collect_all_safe_resources_in_reach
from randovania.resolver.item_pool import calculate_item_pool, calculate_available_pickups, \
    remove_pickup_entry_from_list
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutMode, \
    LayoutRandomizedFlag, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.logic import Logic
from randovania.resolver.random_lib import shuffle
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State, add_resource_gain_to_state

T = TypeVar("T")


def pickup_to_current_resources(pickup: PickupEntry, database: ResourceDatabase) -> CurrentResources:
    return {
        resource: quantity
        for resource, quantity in pickup.resource_gain(database)
    }


def _iterate_previous_states(state: State) -> Iterator[State]:
    while state:
        yield state
        state = state.previous_state


def _state_to_solver_path(final_state: State,
                          game: GameDescription
                          ) -> Tuple[SolverPath, ...]:
    def build_previous_nodes(s: State):
        if s.path_from_previous_state:
            return tuple(
                game.node_name(node) for node in s.path_from_previous_state
                if node is not s.previous_state.node
            )
        else:
            return tuple()

    return tuple(
        SolverPath(
            node_name=game.node_name(state.node, with_world=True),
            previous_nodes=build_previous_nodes(state)
        )
        for state in reversed(list(_iterate_previous_states(final_state)))
    )


def generate_list(data: Dict,
                  seed_number: int,
                  configuration: LayoutConfiguration,
                  status_update: Optional[Callable[[str], None]]
                  ) -> LayoutDescription:
    elevators = randovania.games.prime.claris_randomizer.elevator_list_for_configuration(configuration, seed_number)
    if status_update is None:
        status_update = id

    try:
        with multiprocessing.dummy.Pool(1) as dummy_pool:
            new_patches = _create_patches(
                **{
                    "seed_number": seed_number,
                    "configuration": configuration,
                    "game": data_reader.decode_data(data, elevators, False),
                    "status_update": status_update
                })
            # new_patches = dummy_pool.apply_async(
            #     func=_create_patches,
            #     kwds={
            #         "seed_number": seed_number,
            #         "configuration": configuration,
            #         "game": data_reader.decode_data(data, elevators),
            #         "status_update": status_update
            #     }
            # ).get(120)
    except multiprocessing.TimeoutError:
        raise GenerationFailure(
            "Timeout reached when generating patches.",
            configuration=configuration,
            seed_number=seed_number
        )

    if configuration.logic == LayoutLogic.MINIMAL_RESTRICTIONS and False:
        # For minimal restrictions, the solver path will take paths that are just impossible.
        # Let's just not include a path instead of including a lie.
        solver_path = ()

    else:
        game = data_reader.decode_data(data, elevators)
        final_state_by_resolve = resolver.resolve(
            configuration=configuration,
            game=game,
            patches=new_patches
        )
        if final_state_by_resolve is None:
            # Why is final_state_by_distribution not OK?
            raise GenerationFailure(
                "Generated patches was impossible for the solver.",
                configuration=configuration,
                seed_number=seed_number
            )
        else:
            solver_path = _state_to_solver_path(final_state_by_resolve, game)

    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version=VERSION,
        pickup_mapping=tuple(new_patches.pickup_mapping),
        solver_path=solver_path
    )


Action = Union[ResourceNode, PickupEntry]


def _filter_unassigned_pickup_nodes(nodes: Iterator[Node],
                                    pickup_assignment: PickupAssignment,
                                    ) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode) and node.pickup_index not in pickup_assignment:
            yield node


def _state_with_pickup(state: State,
                       pickup: PickupEntry,) -> State:

    new_state = state.copy()
    add_resource_gain_to_state(new_state, pickup.resource_gain())
    return new_state


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
        escape_state = _state_with_pickup(reach.state, pickup)

        total_pickup_nodes = list(_filter_pickups(filter_reachable(reach.nodes, reach)))
        pickup_nodes = list(_filter_unassigned_pickup_nodes(total_pickup_nodes, pickup_assignment))
        num_nodes = len(pickup_nodes)
        actions_weights = {
            node: len(path)
            for node, path in reach.shortest_path_from(initial_state.node).items()
        }

        try:
            pickup_node = next(pickup_nodes_that_can_reach(_iterate_with_weights(pickup_nodes, actions_weights, rng),
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


def _create_patches(
        seed_number: int,
        configuration: LayoutConfiguration,
        game: GameDescription,
        status_update: Callable[[str], None],
) -> GamePatches:
    rng = Random(seed_number)

    patches = GamePatches({})

    categories = {"translator", "major"}

    if configuration.sky_temple_keys == LayoutRandomizedFlag.VANILLA:
        for i, pickup in enumerate(game.pickup_database.pickups):
            if pickup.item_category == "sky_temple_key":
                patches.pickup_assignment[PickupIndex(i)] = pickup

    logic, state = logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    item_pool = calculate_item_pool(configuration, game)
    available_pickups = tuple(shuffle(rng,
                                      sorted(calculate_available_pickups(item_pool,
                                                                         categories,
                                                                         logic.game.relevant_resources))))
    remaining_items = [
        pickup for pickup in sorted(item_pool)
        if pickup not in available_pickups
    ]

    new_pickup_mapping = _random_assumed_filler(logic, state, patches, available_pickups, rng)
    rng.shuffle(remaining_items)

    for pickup_node in _filter_unassigned_pickup_nodes(game.all_nodes, new_pickup_mapping):
        new_pickup_mapping[pickup_node.pickup_index] = remaining_items.pop()

    assert not remaining_items

    return GamePatches(new_pickup_mapping)


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)


def _filter_events(nodes: Iterator[Node]) -> Iterator[EventNode]:
    return filter(lambda node: isinstance(node, EventNode), nodes)


def is_pickup_node_available(pickup_node: PickupNode, logic: Logic, patches: GamePatches) -> bool:
    if logic.configuration.mode == LayoutMode.MAJOR_ITEMS:
        pickup = logic.game.resource_database.pickups[pickup_node.pickup_index.index]
        if pickup.item_category not in {"sky_temple_key", "translator", "major", "temple_key", "energy_tank"}:
            return False
    return patches.pickup_mapping[pickup_node.pickup_index.index] is None


class VictoryReached(Exception):
    def __init__(self, state: State):
        self.state = state


def _can_reach_safe_node(with_event_state: State, logic: Logic, reach: ResolverReach) -> bool:
    return any(
        reach.is_safe(target_node) and requirements.satisfied(with_event_state.resources,
                                                              with_event_state.resource_database)
        for target_node, requirements in logic.game.potential_nodes_from(with_event_state.node)
    )


def reach_with_all_safe_events(logic: Logic,
                               patches: GamePatches,
                               initial_state: State,
                               ) -> Tuple[State, ResolverReach]:
    dangerous_resources = logic.game.dangerous_resources

    state = initial_state

    reach = None
    has_safe_event = True
    while has_safe_event:
        state.node = initial_state.node
        reach = ResolverReach.calculate_reach(logic, state)
        has_safe_event = False

        new_state = state
        for action in reach.possible_actions(state):
            new_resource = action.resource()
            if is_resource_node(action) and new_resource not in dangerous_resources and new_state.has_resource(
                    new_state):
                potential_new_state = new_state.act_on_node(action, patches.pickup_mapping)
                if _can_reach_safe_node(potential_new_state,
                                        logic,
                                        reach):
                    new_state = potential_new_state
                    has_safe_event = True
        state = new_state

    return state, reach


def _does_pickup_satisfies(pickup: PickupEntry,
                           interesting_resources: FrozenSet[ResourceInfo],
                           database: ResourceDatabase,
                           ) -> bool:
    return any(resource in interesting_resources
               for resource, _ in pickup.resource_gain(database))


def _get_items_that_satisfies(available_item_pickups: Iterator[PickupEntry],
                              pickup_state_without_item: State,
                              pickup_reach_without_item: ResolverReach,
                              database: ResourceDatabase,
                              ) -> Iterator[PickupEntry]:
    interesting_resources = calculate_interesting_resources(
        pickup_reach_without_item.satisfiable_requirements,
        pickup_state_without_item.resources,
        pickup_state_without_item.resource_database)

    for pickup in available_item_pickups:
        if _does_pickup_satisfies(pickup, interesting_resources, database):
            yield pickup


def _add_item_to_node(item: PickupEntry,
                      node: PickupNode,
                      patches: GamePatches,
                      database: ResourceDatabase,
                      ) -> GamePatches:
    pickup_mapping = copy.copy(patches.pickup_mapping)

    assert pickup_mapping[node.pickup_index.index] is None
    pickup_mapping[node.pickup_index.index] = database.pickups.index(item)

    return GamePatches(
        patches.item_loss_enabled,
        pickup_mapping
    )


def _num_items_in_patches(patches: GamePatches) -> int:
    return len([x for x in patches.pickup_mapping if x is not None])


def _iterate_with_weights(potential_actions: List[T],
                          actions_weights: Dict[T, int],
                          rng: Random) -> Iterator[T]:
    weights = [actions_weights[action] for action in potential_actions]

    while potential_actions:
        pickup_node = rng.choices(potential_actions, weights)[0]

        # Remove the pickup_node from the potential list, along with it's weight
        index = potential_actions.index(pickup_node)
        potential_actions.pop(index)
        weights.pop(index)

        yield pickup_node


def _pickup_indices_in_reach(reach: ResolverReach) -> Iterator[PickupIndex]:
    for node in reach.nodes:
        if isinstance(node, PickupNode):
            yield node.pickup_index


def _empty_pickup_indices(pickup_indices: Iterable[PickupIndex],
                          patches: GamePatches,
                          ) -> Iterator[PickupIndex]:
    """
    Iterates over all PickupIndex that have no item defined in the given patches
    :param pickup_indices:
    :param patches:
    :return:
    """
    for pickup in pickup_indices:
        if patches.pickup_mapping[pickup.index] is None:
            yield pickup


def _add_item_to_pickup_index(action: PickupEntry, state: State,
                              pickup_index: PickupIndex, patches: GamePatches,
                              database: ResourceDatabase,
                              ) -> Tuple[State, GamePatches]:
    pickup_mapping = copy.copy(patches.pickup_mapping)

    assert pickup_mapping[pickup_index.index] is None
    pickup_mapping[pickup_index.index] = database.pickups.index(action)

    new_state = state.copy()
    for pickup_resource, quantity in action.resource_gain(database):
        new_state.resources[pickup_resource] = new_state.resources.get(pickup_resource, 0)
        new_state.resources[pickup_resource] += quantity

    new_patches = GamePatches(patches.item_loss_enabled, pickup_mapping)

    return new_state, new_patches


def _count_by_type(iterable: Iterable[T]) -> Dict[type, int]:
    result = {}
    for item in iterable:
        t = type(item)
        result[t] = result.get(t, 0) + 1

    return {
        t.__name__: v
        for t, v in sorted(result.items(), key=lambda x: x[0].__name__)
    }


def _calculate_weights(potential_actions: Set[Action], components) -> Dict[Action, int]:
    result = {}

    component_for_node = {}
    for component in components:
        for node in component:
            component_for_node[node] = component

    print(">>>>>")
    for action in potential_actions:
        if isinstance(action, PickupEntry):
            result[action] = 1
        else:
            result[action] = len(component_for_node[action])
            print("Weight for {} is {}".format(action.name, result[action]))
    return result


def distribute_one_item(
        logic: Logic,
        state: State,
        patches: GamePatches,
        available_item_pickups: Tuple[PickupEntry, ...],
        rng: Random,
        status_update: Callable[[str], None],
) -> Optional[Tuple[GamePatches, Tuple[PickupEntry, ...], State]]:
    start_time = debug.print_distribute_one_item(state, available_item_pickups)

    state, reach = reach_with_all_safe_events(logic, patches, state)

    if logic.game.victory_condition.satisfied(state.resources, state.resource_database):
        return patches, available_item_pickups, state

    potential_actions = set(reach.possible_actions(state))
    potential_actions |= set(_get_items_that_satisfies(available_item_pickups,
                                                       state,
                                                       reach,
                                                       logic.game.resource_database))

    actions_weights = _calculate_weights(potential_actions, reach._strongly_connected_components)
    print("Potential actions: {}".format(_count_by_type(potential_actions)))

    for action in _iterate_with_weights(list(sorted(potential_actions)),
                                        actions_weights,
                                        rng):

        if isinstance(action, PickupEntry):
            # Let's shuffle a pickup somewhere!
            all_pickup_indices = set(state.collected_pickup_indices)
            all_pickup_indices |= set(_pickup_indices_in_reach(reach))

            for pickup_index in shuffle(rng, _empty_pickup_indices(all_pickup_indices, patches)):
                new_state, new_patches = _add_item_to_pickup_index(action, state, pickup_index,
                                                                   patches, logic.game.resource_database)
                debug.print_distribute_fill_pickup_index(pickup_index, action, logic)
                status_update("Distributed {} items so far...".format(_num_items_in_patches(new_patches)))

                new_result = distribute_one_item(
                    logic,
                    new_state,
                    new_patches,
                    remove_pickup_entry_from_list(available_item_pickups, action),
                    rng,
                    status_update
                )
                if new_result is not None:
                    return new_result

        else:
            # We decided just to pick a new dangerous action
            new_result = distribute_one_item(
                logic,
                state.act_on_node(action, patches.pickup_mapping),
                patches,
                available_item_pickups,
                rng,
                status_update
            )
            if new_result is not None:
                return new_result

    status_update("Rollback. Only {} items now".format(_num_items_in_patches(patches)))


def _old_code():
    for pickup_node in _iterate_with_weights(potential_pickup_nodes,
                                             node_weights,
                                             rng):
        assert patches.pickup_mapping[
                   pickup_node.pickup_index.index] is None, "Node with assigned pickup being considered again"

        # This is the State that can act on the pickup node, with all events we want to collect
        before_state = pickups_with_path[pickup_node]

        pickup_state_without_item = before_state.act_on_node(pickup_node, patches.pickup_mapping)
        pickup_reach_without_item = ResolverReach.calculate_reach(logic, pickup_state_without_item)

        for item in shuffle(rng, _get_items_that_satisfies(available_item_pickups,
                                                           pickup_state_without_item,
                                                           pickup_reach_without_item,
                                                           logic.game.resource_database)):

            new_patches = _add_item_to_node(item, pickup_node, patches, logic.game.resource_database)
            pickup_state_with_item = before_state.act_on_node(pickup_node, new_patches.pickup_mapping)
            pickup_reach_with_item = ResolverReach.calculate_reach(logic, pickup_state_with_item)

            if pickup_reach_without_item.nodes == pickup_reach_with_item.nodes:
                continue

            debug.print_distribute_place_item(pickup_node, item, logic)
            status_update("Distributed {} items so far...".format(_num_items_in_patches(new_patches)))
            recursive_result = distribute_one_item(
                logic,
                pickup_state_with_item,
                new_patches,
                remove_pickup_entry_from_list(available_item_pickups, item),
                rng,
                status_update
            )
            if recursive_result:
                return recursive_result
            else:
                status_update("Rollback. Only {} items now".format(_num_items_in_patches(patches)))

    debug.print_distribute_one_item_rollback(state)
    return None
