import collections
import copy
from random import Random
from typing import List, Tuple, Iterator, Optional, FrozenSet, Callable, TypeVar, Dict

from randovania import VERSION
from randovania.resolver import debug, resolver, data_reader
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_description import GameDescription, calculate_interesting_resources
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutEnabledFlag, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.logic import Logic
from randovania.resolver.node import EventNode, Node, PickupNode
from randovania.resolver.reach import Reach
from randovania.resolver.requirements import RequirementSet
from randovania.resolver.resources import ResourceInfo, ResourceDatabase, CurrentResources, PickupEntry
from randovania.resolver.state import State


def pickup_to_current_resources(pickup: PickupEntry, database: ResourceDatabase) -> CurrentResources:
    return {
        resource: quantity
        for resource, quantity in pickup.resource_gain(database)
    }


T = TypeVar('T')


def shuffle(rng: Random, x: Iterator[T]) -> List[T]:
    result = list(x)
    rng.shuffle(result)
    return result


def expand_layout_logic(logic: LayoutLogic):
    if logic == LayoutLogic.NO_GLITCHES:
        return 0, set()
    else:
        raise Exception("Unsupported logic")


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


def calculate_available_pickups(game: GameDescription) -> Iterator[PickupEntry]:
    unique_stuff = {
        frozenset(pickup_to_current_resources(pickup, game.resource_database).items()): pickup
        for pickup in game.resource_database.pickups
    }
    for pickup in unique_stuff.values():
        yield pickup


def generate_list(data: Dict,
                  configuration: LayoutConfiguration,
                  status_update: Callable[[str], None]
                  ) -> LayoutDescription:
    difficulty_level, tricks_enabled = expand_layout_logic(configuration.logic)

    new_patches = _create_patches(configuration, data, difficulty_level, status_update, tricks_enabled)

    game = data_reader.decode_data(data, [])
    final_state_by_resolve = resolver.resolve(
        difficulty_level=difficulty_level,
        tricks_enabled=tricks_enabled,
        game=game,
        patches=new_patches
    )

    if final_state_by_resolve is None:
        # Why is final_state_by_distribution not OK?
        raise Exception("We just created an item distribution we believe is impossible. What?")

    return LayoutDescription(
        configuration=configuration,
        version=VERSION,
        pickup_mapping=tuple(new_patches.pickup_mapping),
        solver_path=_state_to_solver_path(final_state_by_resolve, game)
    )


def _create_patches(configuration: LayoutConfiguration,
                    data: Dict,
                    difficulty_level: int,
                    status_update: Callable[[str], None],
                    tricks_enabled):
    rng = Random(configuration.seed_number)
    game = data_reader.decode_data(data, [])
    patches = GamePatches(
        configuration.item_loss == LayoutEnabledFlag.ENABLED,
        [None] * len(game.resource_database.pickups)
    )

    available_pickups = tuple(shuffle(rng, sorted(calculate_available_pickups(game))))
    remaining_items = [
        pickup
        for pickup in game.resource_database.pickups
        if pickup not in available_pickups
    ]

    logic, state = logic_bootstrap(difficulty_level, game, patches, tricks_enabled)
    logic.game.simplify_connections(state.resources)

    new_patches, non_added_items, final_state_by_distribution = distribute_one_item(
        logic, state, patches, available_pickups, rng, status_update=status_update)
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


class VictoryReached(Exception):
    def __init__(self, state: State):
        self.state = state


def find_all_pickups_via_most_events(logic: Logic,
                                     patches: GamePatches,
                                     initial_state: State,
                                     victory_condition: RequirementSet,
                                     ) -> Dict[PickupNode, Tuple[EventNode, ...]]:
    paths = {}
    checked = set()

    queue: collections.OrderedDict[State, Tuple[EventNode, ...]] = collections.OrderedDict()
    queue[initial_state] = ()

    while queue:
        state, path = queue.popitem(last=False)
        checked.add(state.node)

        if victory_condition.satisfied(state.resources):
            raise VictoryReached(state)

        reach = Reach.calculate_reach(logic, state)
        actions = list(reach.possible_actions(state))

        for event in _filter_events(actions):
            if event not in checked:
                queue[state.act_on_node(event, patches.pickup_mapping)] = path + (event,)

        for pickup in _filter_pickups(actions):
            paths[pickup] = path

    return paths


def _does_pickup_satisfies(pickup: PickupEntry,
                           interesting_resources: FrozenSet[ResourceInfo],
                           database: ResourceDatabase,
                           ) -> bool:
    return any(resource in interesting_resources
               for resource, _ in pickup.resource_gain(database))


def _get_items_that_satisfies(available_item_pickups: Iterator[PickupEntry],
                              interesting_resources: FrozenSet[ResourceInfo],
                              database: ResourceDatabase,
                              ) -> Iterator[PickupEntry]:
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


def distribute_one_item(
        logic: Logic,
        state: State,
        patches: GamePatches,
        available_item_pickups: Tuple[PickupEntry],
        rng: Random,
        status_update: Callable[[str], None],
) -> Optional[Tuple[GamePatches, Tuple[PickupEntry], State]]:
    debug.print_distribute_one_item(state, available_item_pickups)

    try:
        pickups_with_path = find_all_pickups_via_most_events(
            logic, patches, state, logic.game.victory_condition)

    except VictoryReached as v:
        return patches, available_item_pickups, v.state

    for pickup_node in shuffle(rng, sorted(pickups_with_path.keys())):
        assert patches.pickup_mapping[
                   pickup_node.pickup_index.index] is None, "Node with assigned pickup being considered again"

        new_state = state
        for action in pickups_with_path[pickup_node]:
            assert isinstance(action, EventNode)
            new_state = new_state.act_on_node(action, patches.pickup_mapping)

        reach = Reach.calculate_reach(logic, new_state)
        calculate_interesting_resources(reach.satisfiable_requirements,
                                        state.resources)

        for item in _get_items_that_satisfies(available_item_pickups,
                                              calculate_interesting_resources(reach.satisfiable_requirements,
                                                                             state.resources),
                                              logic.game.resource_database):

            new_patches = _add_item_to_node(item, pickup_node, patches, logic.game.resource_database)
            next_state = new_state.act_on_node(pickup_node, new_patches.pickup_mapping)

            before_reach = Reach.calculate_reach(logic, new_state.act_on_node(pickup_node, patches.pickup_mapping))
            after_reach = Reach.calculate_reach(logic, next_state)
            if before_reach.nodes == after_reach.nodes:
                continue

            status_update("Distributed {} items so far...".format(_num_items_in_patches(new_patches)))
            recursive_result = distribute_one_item(
                logic,
                next_state,
                new_patches,
                tuple(pickup for pickup in available_item_pickups if pickup is not item),
                rng,
                status_update
            )
            if recursive_result:
                return recursive_result
            else:
                status_update("Rollback. Only {} items now".format(_num_items_in_patches(patches)))

    debug.print_distribute_one_item_rollback([])
    return None
