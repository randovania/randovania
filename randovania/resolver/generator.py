import collections
import copy
import itertools
import pprint
from random import Random
from typing import List, Tuple, NamedTuple, Iterator, Optional, FrozenSet, Callable, TypeVar, Dict, Set

from randovania import VERSION
from randovania.resolver import debug, resolver, data_reader
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_description import GameDescription, calculate_interesting_resources
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutEnabledFlag, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.logic import Logic
from randovania.resolver.node import EventNode, Node, PickupNode, ResourceNode
from randovania.resolver.reach import Reach
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


class ItemSlot(NamedTuple):
    required_actions: Tuple[Node, ...]
    available_actions: Tuple[ResourceNode, ...]
    state: State
    reach: Reach
    interesting_resources: FrozenSet[ResourceInfo]


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)


def _filter_events(nodes: Iterator[Node]) -> Iterator[EventNode]:
    return filter(lambda node: isinstance(node, EventNode), nodes)


def find_all_pickups_via_most_events(logic: Logic,
                                     patches: GamePatches,
                                     initial_state: State,
                                     ) -> Dict[PickupNode, Tuple[EventNode, ...]]:

    paths = {}
    checked = set()

    queue: collections.OrderedDict[State, Tuple[EventNode, ...]] = collections.OrderedDict()
    queue[initial_state] = ()

    while queue:
        state, path = queue.popitem(last=False)
        checked.add(state.node)

        reach = Reach.calculate_reach(logic, state)
        actions = list(reach.possible_actions(state))

        for event in _filter_events(actions):
            if event not in checked:
                queue[state.act_on_node(event, patches.pickup_mapping)] = path + (event,)

        for pickup in _filter_pickups(actions):
            paths[pickup] = path

    return paths


_MAXIMUM_DEPTH = 2


def find_potential_item_slots(logic: Logic,
                              patches: GamePatches,
                              state: State,
                              actions_required: Tuple[Node, ...] = (),
                              current_depth: int = 0,
                              maximum_depth: int = _MAXIMUM_DEPTH,
                              ) -> Iterator[ItemSlot]:
    reach = Reach.calculate_reach(logic, state)

    actions = list(reach.possible_actions(state))
    new_depth = current_depth + 1
    if len(actions) == 1:
        maximum_depth += 1

    available_pickups = tuple(_filter_pickups(actions))
    debug.print_potential_item_slots(state, actions, available_pickups, current_depth, maximum_depth)

    if available_pickups:
        yield ItemSlot(required_actions=actions_required,
                       available_actions=tuple(actions),
                       state=state,
                       reach=reach,
                       interesting_resources=calculate_interesting_resources(reach.satisfiable_requirements,
                                                                             state.resources),
                       )

    # Enough pickups, just try to use one of then already
    if new_depth > maximum_depth or len(available_pickups) > 10:
        return

    for action in actions:
        yield from find_potential_item_slots(
            logic,
            patches,
            state.act_on_node(action, patches.pickup_mapping),
            actions_required + (action,),
            current_depth=new_depth,
            maximum_depth=maximum_depth
        )


def does_pickup_satisfies(pickup: PickupEntry,
                          interesting_resources: FrozenSet[ResourceInfo],
                          database: ResourceDatabase,
                          ) -> bool:
    return any(resource in interesting_resources
               for resource, _ in pickup.resource_gain(database))


def get_items_that_satisfies(available_item_pickups: Iterator[PickupEntry],
                             interesting_resources: FrozenSet[ResourceInfo],
                             database: ResourceDatabase,
                             ) -> Iterator[PickupEntry]:
    for pickup in available_item_pickups:
        if does_pickup_satisfies(pickup, interesting_resources, database):
            yield pickup


def add_item_to_node(item: PickupEntry, node: PickupNode,
                     patches: GamePatches, database: ResourceDatabase) -> GamePatches:
    pickup_mapping = copy.copy(patches.pickup_mapping)

    assert pickup_mapping[node.pickup_index.index] is None
    pickup_mapping[node.pickup_index.index] = database.pickups.index(item)

    return GamePatches(
        patches.item_loss_enabled,
        pickup_mapping
    )


def _num_items_in_patches(patches: GamePatches) -> int:
    return len([x for x in patches.pickup_mapping if x is not None])


def is_victory_condition_reachable(logic: Logic,
                                   state: State,
                                   patches: GamePatches,
                                   potential_item_slots: List[ItemSlot],
                                   ) -> bool:
    for item_option in potential_item_slots:
        for event in _filter_events(item_option.available_actions):
            with_event = state.act_on_node(event, patches.pickup_mapping)
            if logic.game.victory_condition.satisfied(with_event.resources):
                return True

    return False


def find_available_pickup_slots(potential_item_slots: List[ItemSlot]
                                ) -> List[PickupNode]:
    return list(sorted(frozenset(itertools.chain.from_iterable(
        _filter_pickups(item_option.available_actions)
        for item_option in potential_item_slots
    ))))


def _merge_interesting_resources(potential_item_slots: List[ItemSlot]) -> FrozenSet[ResourceInfo]:
    return frozenset(itertools.chain.from_iterable(
        item_option.interesting_resources
        for item_option in potential_item_slots
    ))


def add_item_and_act(item: PickupEntry,
                     item_slot: ItemSlot,
                     pickup_node: PickupNode,
                     new_patches: GamePatches,
                     logic: Logic,
                     state: State,
                     available_item_pickups: Tuple[PickupEntry],
                     rng: Random,
                     status_update: Callable[[str], None],
                     ):
    for action in item_slot.required_actions:
        state = state.act_on_node(action, new_patches.pickup_mapping)

    # Handle when the pickup_node we selected was a required action
    if pickup_node not in item_slot.required_actions:
        state = state.act_on_node(pickup_node, new_patches.pickup_mapping)

    new_reach = Reach.calculate_reach(logic, state)
    if new_reach.nodes == item_slot.reach.nodes:
        return None

    new_available_item_pickups = tuple(pickup for pickup in available_item_pickups if pickup is not item)

    if not new_available_item_pickups:
        return new_patches, new_available_item_pickups, state

    status_update("Distributed {} items so far...".format(_num_items_in_patches(new_patches)))
    return distribute_one_item(logic, state,
                               new_patches, new_available_item_pickups,
                               rng,
                               status_update=status_update)


def distribute_one_item(logic: Logic,
                        state: State,
                        patches: GamePatches,
                        available_item_pickups: Tuple[PickupEntry],
                        rng: Random,
                        status_update: Callable[[str], None],
                        ) -> Optional[Tuple[GamePatches, Tuple[PickupEntry], State]]:
    debug.print_distribute_one_item(state, available_item_pickups)

    potential_item_slots: List[ItemSlot] = shuffle(
        rng,
        find_potential_item_slots(logic, patches, state))

    # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    # for pickup, paths in find_all_pickups_via_most_events(logic, patches, state).items():
    #     print("==============")
    #     print(debug.n(pickup))
    #     pprint.pprint(paths)

    if is_victory_condition_reachable(logic, state, patches, potential_item_slots):
        return patches, available_item_pickups, state

    available_pickups_spots = shuffle(rng, find_available_pickup_slots(potential_item_slots))

    item_options = list(get_items_that_satisfies(available_item_pickups,
                                                 _merge_interesting_resources(potential_item_slots),
                                                 logic.game.resource_database))

    debug.print_distribute_one_item_detail(potential_item_slots,
                                           available_pickups_spots,
                                           available_item_pickups,
                                           item_options)

    for item in item_options:
        for pickup_node in available_pickups_spots:
            for item_slot in potential_item_slots:
                if pickup_node not in item_slot.available_actions or \
                        not does_pickup_satisfies(item,
                                                  item_slot.interesting_resources,
                                                  logic.game.resource_database):
                    continue

                debug.print_distribute_place_item(item, pickup_node)
                recursive_result = add_item_and_act(
                    item,
                    item_slot,
                    pickup_node,
                    new_patches=add_item_to_node(item, pickup_node, patches, logic.game.resource_database),
                    logic=logic,
                    state=state,
                    available_item_pickups=available_item_pickups,
                    rng=rng,
                    status_update=status_update
                )
                if recursive_result:
                    return recursive_result

                status_update("Rollback. Only {} items now".format(_num_items_in_patches(patches)))
                # TODO: boost the additional_requirements for _something_ so we never try this again

    debug.print_distribute_one_item_rollback(item_options)
    logic.additional_requirements[state.node] = Reach.calculate_reach(logic, state).satisfiable_as_requirement_set
    return None
