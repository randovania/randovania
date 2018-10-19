import collections
import copy
import multiprocessing.dummy
from random import Random
from typing import List, Tuple, Iterator, Optional, FrozenSet, Callable, Dict

import randovania.games.prime.claris_randomizer
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription, calculate_interesting_resources
from randovania.game_description.node import EventNode, Node, PickupNode
from randovania.game_description.requirements import RequirementSet
from randovania.game_description.resources import ResourceInfo, ResourceDatabase, CurrentResources, PickupEntry
from randovania.resolver import debug, resolver, item_pool
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.item_pool import calculate_item_pool, calculate_available_pickups, \
    remove_pickup_entry_from_list
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutEnabledFlag, LayoutMode, \
    LayoutRandomizedFlag, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.logic import Logic
from randovania.resolver.random_lib import shuffle
from randovania.resolver.reach import Reach
from randovania.resolver.state import State


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
            new_patches = dummy_pool.apply_async(
                func=_create_patches,
                kwds={
                    "seed_number": seed_number,
                    "configuration": configuration,
                    "game": data_reader.decode_data(data, elevators),
                    "status_update": status_update
                }
            ).get(120)
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


def _create_patches(
        seed_number: int,
        configuration: LayoutConfiguration,
        game: GameDescription,
        status_update: Callable[[str], None],
) -> GamePatches:
    rng = Random(seed_number)

    patches = GamePatches(
        configuration.item_loss == LayoutEnabledFlag.ENABLED,
        [None] * len(game.resource_database.pickups)
    )

    categories = {"translator", "major", "temple_key"}

    if configuration.sky_temple_keys == LayoutRandomizedFlag.VANILLA:
        for i, pickup in enumerate(game.resource_database.pickups):
            if pickup.item_category == "sky_temple_key":
                patches.pickup_mapping[i] = i
    else:
        categories.add("sky_temple_key")

    item_pool = calculate_item_pool(configuration, game)
    available_pickups = tuple(shuffle(rng, sorted(calculate_available_pickups(item_pool, categories))))
    remaining_items = [
        pickup for pickup in sorted(item_pool)
        if pickup not in available_pickups
    ]

    logic, state = logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    new_patches, non_added_items, final_state_by_distribution = distribute_one_item(
        logic,
        state,
        patches,
        available_pickups,
        rng,
        status_update=status_update)

    remaining_items.extend(non_added_items)

    rng.shuffle(remaining_items)

    for i, index in enumerate(new_patches.pickup_mapping):
        if index is not None:
            continue
        new_patches.pickup_mapping[i] = game.resource_database.pickups.index(remaining_items.pop())

    assert not remaining_items

    return new_patches


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


def _can_reach_safe_node(with_event_state: State, logic: Logic, reach: Reach) -> bool:
    return any(
        reach.is_safe(target_node) and requirements.satisfied(with_event_state.resources,
                                                              with_event_state.resource_database)
        for target_node, requirements in logic.game.potential_nodes_from(with_event_state.node)
    )


def find_all_pickups_via_most_events(logic: Logic,
                                     patches: GamePatches,
                                     initial_state: State,
                                     victory_condition: RequirementSet,
                                     ) -> Dict[PickupNode, State]:
    paths = {}
    checked = set()

    queue: collections.OrderedDict[Node, State] = collections.OrderedDict()
    queue[initial_state.node] = initial_state

    while queue:
        _, state = queue.popitem(last=False)
        checked.add(state.node)

        reach = None
        has_safe_event = True
        while has_safe_event:
            reach = Reach.calculate_reach(logic, state)
            if victory_condition.satisfied(state.resources, state.resource_database):
                raise VictoryReached(state)

            has_safe_event = False

            for action in reach.possible_actions(state):
                if isinstance(action, EventNode) and (
                        action.resource(state.resource_database) not in logic.game.dangerous_resources):

                    if _can_reach_safe_node(state.act_on_node(action, patches.pickup_mapping),
                                            logic,
                                            reach):
                        state.resources = state.collect_resource_node(action, patches.pickup_mapping).resources
                        has_safe_event = True

        for action in sorted(reach.possible_actions(state)):
            if isinstance(action, EventNode):
                if action not in checked:
                    assert not reach.is_safe(action)
                    queue[action] = state.act_on_node(action, patches.pickup_mapping)
            else:
                paths[action] = state

    return paths


def _does_pickup_satisfies(pickup: PickupEntry,
                           interesting_resources: FrozenSet[ResourceInfo],
                           database: ResourceDatabase,
                           ) -> bool:
    return any(resource in interesting_resources
               for resource, _ in pickup.resource_gain(database))


def _get_items_that_satisfies(available_item_pickups: Iterator[PickupEntry],
                              pickup_state_without_item: State,
                              pickup_reach_without_item: Reach,
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


def _iterate_with_weights(potential_pickup_nodes: List[PickupNode],
                          pickup_weights: Dict[PickupNode, int],
                          rng: Random) -> Iterator[PickupNode]:
    weights = [pickup_weights[pickup_node] for pickup_node in potential_pickup_nodes]

    while potential_pickup_nodes:
        pickup_node = rng.choices(potential_pickup_nodes, weights)[0]

        # Remove the pickup_node from the potential list, along with it's weight
        index = potential_pickup_nodes.index(pickup_node)
        potential_pickup_nodes.pop(index)
        weights.pop(index)

        yield pickup_node


def distribute_one_item(
        logic: Logic,
        state: State,
        patches: GamePatches,
        available_item_pickups: Tuple[PickupEntry, ...],
        rng: Random,
        status_update: Callable[[str], None],
) -> Optional[Tuple[GamePatches, Tuple[PickupEntry, ...], State]]:
    start_time = debug.print_distribute_one_item(state, available_item_pickups)

    try:
        pickups_with_path = find_all_pickups_via_most_events(
            logic, patches, state, logic.game.victory_condition)

    except VictoryReached as v:
        return patches, available_item_pickups, v.state

    potential_pickup_nodes = list(sorted(pickups_with_path.keys(), reverse=True))

    # Increment how many times we've seen each pickup node
    for pickup_node in potential_pickup_nodes:
        logic.node_sightings[pickup_node] += 1

    # Our weighting currently favors more nodes seem for the first time
    # FIXME: Using ** 2 made glitchless seed 50000 break on validation again...
    node_weights = {pickup_node: 1000 / (logic.node_sightings[pickup_node] ** 1)
                    for pickup_node in potential_pickup_nodes}

    # Calculating Reach for all nodes is kinda too CPU intensive, unfortunately.
    # TODO: better algorithm that calculates multiple reaches at the same time?
    debug.print_distribute_one_item_detail(potential_pickup_nodes, start_time)

    for pickup_node in _iterate_with_weights(potential_pickup_nodes,
                                             node_weights,
                                             rng):
        assert patches.pickup_mapping[
                   pickup_node.pickup_index.index] is None, "Node with assigned pickup being considered again"

        # This is the State that can act on the pickup node, with all events we want to collect
        before_state = pickups_with_path[pickup_node]

        pickup_state_without_item = before_state.act_on_node(pickup_node, patches.pickup_mapping)
        pickup_reach_without_item = Reach.calculate_reach(logic, pickup_state_without_item)

        for item in shuffle(rng, _get_items_that_satisfies(available_item_pickups,
                                                           pickup_state_without_item,
                                                           pickup_reach_without_item,
                                                           logic.game.resource_database)):

            new_patches = _add_item_to_node(item, pickup_node, patches, logic.game.resource_database)
            pickup_state_with_item = before_state.act_on_node(pickup_node, new_patches.pickup_mapping)
            pickup_reach_with_item = Reach.calculate_reach(logic, pickup_state_with_item)

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
