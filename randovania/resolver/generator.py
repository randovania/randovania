import copy
import itertools
import random
from typing import List, Set, Tuple, NamedTuple, Iterator, Optional, FrozenSet

from randovania.resolver import debug
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_description import GameDescription, calculate_interesting_resources
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import Logic
from randovania.resolver.node import EventNode, Node, PickupNode
from randovania.resolver.reach import Reach
from randovania.resolver.resources import ResourceInfo, ResourceDatabase, CurrentResources, PickupEntry
from randovania.resolver.state import State


def pickup_to_current_resources(pickup: PickupEntry, database: ResourceDatabase) -> CurrentResources:
    return {
        resource: quantity
        for resource, quantity in pickup.resource_gain(database)
    }


def generate_list(difficulty_level: int,
                  tricks_enabled: Set[int],
                  game: GameDescription,
                  patches: GamePatches) -> GamePatches:
    patches = GamePatches(
        patches.item_loss_enabled,
        [None] * len(game.resource_database.pickups)
    )

    available_pickups = list({
                                 frozenset(pickup_to_current_resources(pickup, game.resource_database).items()): pickup
                                 for pickup in game.resource_database.pickups
                             }.values())

    logic, state = logic_bootstrap(difficulty_level, game, patches, tricks_enabled)
    logic.game.simplify_connections(state.resources)

    return distribute_one_item(logic, state, patches, available_pickups)


class ItemSlot(NamedTuple):
    available_pickups: Tuple[PickupNode, ...]
    interesting_resources: FrozenSet[ResourceInfo]
    required_actions: Tuple[Node, ...]
    expected_resources: CurrentResources
    events: Tuple[EventNode, ...]


def _filter_pickups(nodes: Iterator[Node]) -> Tuple[PickupNode, ...]:
    return tuple(
        node
        for node in nodes
        if isinstance(node, PickupNode)
    )


def _filter_events(nodes: Iterator[Node]) -> Tuple[EventNode, ...]:
    return tuple(
        node
        for node in nodes
        if isinstance(node, EventNode)
    )


_MAXIMUM_DEPTH = 2


def find_potential_item_slots(logic: Logic,
                              patches: GamePatches,
                              state: State,
                              actions_required: Tuple[Node, ...] = (),
                              current_depth: int = 0) -> Iterator[ItemSlot]:
    reach = Reach.calculate_reach(logic, state)

    actions = list(reach.possible_actions(state))
    new_depth = current_depth if len(actions) == 1 else current_depth + 1

    if new_depth > _MAXIMUM_DEPTH:
        return

    available_pickups = _filter_pickups(actions)
    debug.print_potential_item_slots(state, actions, available_pickups, current_depth, _MAXIMUM_DEPTH)

    if available_pickups:
        yield ItemSlot(available_pickups,
                       calculate_interesting_resources(reach.satisfiable_requirements,
                                                       state.resources),
                       actions_required,
                       copy.copy(state.resources),
                       _filter_events(actions)
                       )

    # Enough pickups, just try to use one of then already
    if len(available_pickups) > 10:
        return

    for action in actions:
        yield from find_potential_item_slots(
            logic,
            patches,
            state.act_on_node(action, patches.pickup_mapping),
            actions_required + (action,),
            new_depth
        )


def does_pickup_satisfies(pickup: PickupEntry,
                          interesting_resources: FrozenSet[ResourceInfo],
                          database: ResourceDatabase,
                          ) -> bool:
    return any(resource in interesting_resources
               for resource, _ in pickup.resource_gain(database))


def get_items_that_satisfies(available_item_pickups: List[PickupEntry],
                             interesting_resources: FrozenSet[ResourceInfo],
                             database: ResourceDatabase,
                             ) -> Iterator[PickupEntry]:
    result_pickup_list = copy.copy(available_item_pickups)
    random.shuffle(result_pickup_list)  # TODO: random

    for pickup in result_pickup_list:
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


def distribute_one_item(logic: Logic, state: State,
                        patches: GamePatches, available_item_pickups: List[PickupEntry]) -> Optional[GamePatches]:
    if logic.game.victory_condition.satisfied(state.resources) or not available_item_pickups:
        return patches

    debug.print_distribute_one_item(state)

    potential_item_slots: List[ItemSlot] = list(find_potential_item_slots(
        logic,
        patches,
        state))
    random.shuffle(potential_item_slots)  # TODO: random

    for item_option in potential_item_slots:
        for event in item_option.events:
            with_event = state.act_on_node(event, patches.pickup_mapping)
            if logic.game.victory_condition.satisfied(with_event.resources):
                return patches

    interesting_resources = frozenset(itertools.chain.from_iterable(
        item_option.interesting_resources
        for item_option in potential_item_slots
    ))
    available_pickups_spots = list(frozenset(itertools.chain.from_iterable(
        item_option.available_pickups
        for item_option in potential_item_slots
    )))
    random.shuffle(available_pickups_spots)  # TODO: random

    debug.print_distribute_one_item_detail(potential_item_slots, available_pickups_spots, available_item_pickups)

    item_log = []
    for item in get_items_that_satisfies(available_item_pickups, interesting_resources, logic.game.resource_database):
        item_log.append(item)

        for pickup_node in available_pickups_spots:
            for item_option in potential_item_slots:
                if pickup_node not in item_option.available_pickups or \
                        not does_pickup_satisfies(item,
                                                  item_option.interesting_resources,
                                                  logic.game.resource_database):
                    continue

                debug.print_distribute_place_item(item, pickup_node)
                new_patches = add_item_to_node(item, pickup_node, patches, logic.game.resource_database)

                new_state = state
                for action in item_option.required_actions:
                    new_state = new_state.act_on_node(action, new_patches.pickup_mapping)

                # Handle when the pickup_node we selected was a required action
                if pickup_node not in item_option.required_actions:
                    new_state = new_state.act_on_node(pickup_node, new_patches.pickup_mapping)

                new_available_item_pickups = copy.copy(available_item_pickups)
                new_available_item_pickups.remove(item)

                recursive_patches = distribute_one_item(logic, new_state,
                                                        new_patches, new_available_item_pickups)
                if recursive_patches:
                    return recursive_patches
                # TODO: boost the additional_requirements for _something_ so we never try this again

    debug.print_distribute_one_item_rollback(item_log, interesting_resources, available_item_pickups)
    logic.additional_requirements[state.node] = Reach.calculate_reach(logic, state).satisfiable_as_requirement_set
    return None
