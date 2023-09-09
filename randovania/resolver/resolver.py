from __future__ import annotations

import asyncio
import itertools
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout import filtered_database
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList, state: State,
                               ) -> RequirementList | None:
    items = []
    for item in self.values():
        if item.satisfied(state.resources, state.energy, state.resource_database):
            continue

        # We don't want to mark collecting a pickup/event node as a requirement to collecting that node.
        # This could be interesting for DockLock, as indicating it needs to be unlocked from the other side.
        if item.resource.resource_type in (ResourceType.NODE_IDENTIFIER, ResourceType.EVENT):
            continue

        items.append(item)

    return RequirementList(items)


def _simplify_additional_requirement_set(alternatives: Iterable[RequirementList],
                                         state: State,
                                         ) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state)
        for alternative in alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def _is_action_dangerous(state: State, action: ResourceNode, dangerous_resources: frozenset[ResourceInfo]) -> bool:
    return any(resource in dangerous_resources
               for resource, _ in action.resource_gain_on_collect(state.node_context()))


def _is_major_or_key_pickup_node(action: ResourceNode, state: State) -> bool:
    if isinstance(action, EventPickupNode):
        pickup_node = action.pickup_node
    else:
        pickup_node = action

    if isinstance(pickup_node, PickupNode):
        target = state.patches.pickup_assignment.get(pickup_node.pickup_index)
        return target is not None and (target.pickup.pickup_category.hinted_as_major or
                                       target.pickup.pickup_category.is_key)
    return False


def _should_check_if_action_is_safe(state: State,
                                    action: ResourceNode,
                                    dangerous_resources: frozenset[ResourceInfo]
                                    ) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :param dangerous_resources:
    :return:
    """
    return not _is_action_dangerous(state, action, dangerous_resources) \
        and (isinstance(action, EventNode | EventPickupNode)
             or _is_major_or_key_pickup_node(action, state))


async def _inner_advance_depth(state: State,
                               logic: Logic,
                               status_update: Callable[[str], None],
                               *,
                               reach: ResolverReach | None = None,
                               max_attempts: int | None = None,
                               ) -> tuple[State | None, bool]:
    """

    :param state:
    :param logic:
    :param status_update:
    :param reach: A precalculated reach for the given state
    :return:
    """

    if logic.victory_condition.satisfied(state.resources, state.energy, state.resource_database):
        return state, True

    # Yield back to the asyncio runner, so cancel can do something
    await asyncio.sleep(0)

    if reach is None:
        reach = ResolverReach.calculate_reach(logic, state)

    logic.start_new_attempt(state, reach, max_attempts)
    status_update(f"Resolving... {state.resources.num_resources} total resources")

    major_pickup_actions = []
    lock_actions = []
    dangerous_actions = []
    point_of_no_return_actions = []
    rest_of_actions = []

    for action, energy in reach.possible_actions(state):
        if _should_check_if_action_is_safe(state, action, logic.game.dangerous_resources):
            potential_state = state.act_on_node(action, path=reach.path_to_node(action), new_energy=energy)
            potential_reach = ResolverReach.calculate_reach(logic, potential_state)

            # If we can go back to where we were, it's a simple safe node
            if state.node in potential_reach.nodes:
                new_result = await _inner_advance_depth(
                    state=potential_state,
                    logic=logic,
                    status_update=status_update,
                    reach=potential_reach,
                    max_attempts=max_attempts,
                )

                if new_result[0] is None:
                    additional = logic.get_additional_requirements(action).alternatives

                    logic.set_additional_requirements(
                        state.node,
                        _simplify_additional_requirement_set(additional, state)
                    )
                    logic.log_rollback(state, True, True, logic.get_additional_requirements(state.node))

                # If a safe node was a dead end, we're certainly a dead end as well
                return new_result
            else:
                point_of_no_return_actions.append((action, energy))
                continue

        action_tuple = (action, energy)
        if _is_action_dangerous(state, action, logic.game.dangerous_resources) and isinstance(action, EventNode):
            dangerous_actions.append(action_tuple)
        elif _is_major_or_key_pickup_node(action, state):
            major_pickup_actions.append(action_tuple)
        elif isinstance(action, DockLockNode | EventNode | EventPickupNode):
            lock_actions.append(action_tuple)
        else:
            rest_of_actions.append(action_tuple)

    actions = list(reach.satisfiable_actions(
        state, logic.victory_condition,
        itertools.chain(major_pickup_actions,
                        lock_actions,
                        rest_of_actions,
                        point_of_no_return_actions,
                        dangerous_actions)
    ))
    logic.log_checking_satisfiable_actions(state, actions)
    has_action = False
    for action, energy in actions:
        new_result = await _inner_advance_depth(
            state=state.act_on_node(action, path=reach.path_to_node(action), new_energy=energy),
            logic=logic,
            status_update=status_update,
            max_attempts=max_attempts,
        )

        # We got a positive result. Send it back up
        if new_result[0] is not None:
            return new_result
        else:
            has_action = True

    additional_requirements = reach.satisfiable_requirements

    if has_action:
        additional = set()
        for resource_node in reach.collectable_resource_nodes(state):
            additional |= logic.get_additional_requirements(resource_node).alternatives

        additional_requirements = additional_requirements.union(additional)

    logic.set_additional_requirements(
        state.node,
        _simplify_additional_requirement_set(
            additional_requirements,
            state
        )
    )
    logic.log_rollback(state, has_action, False, logic.get_additional_requirements(state.node))

    return None, has_action


async def advance_depth(state: State, logic: Logic, status_update: Callable[[str], None],
                        max_attempts: int | None = None) -> State | None:
    logic.resolver_start()
    return (await _inner_advance_depth(state, logic, status_update, max_attempts=max_attempts))[0]


def _quiet_print(s):
    pass


def setup_resolver(configuration: BaseConfiguration, patches: GamePatches) -> tuple[State, Logic]:
    game = filtered_database.game_description_for_layout(configuration).get_mutable()
    bootstrap = game.game.generator.bootstrap

    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)

    new_game, starting_state = bootstrap.logic_bootstrap(configuration, game, patches)
    logic = Logic(new_game, configuration)
    starting_state.resources.add_self_as_requirement_to_resources = True

    return starting_state, logic


async def resolve(configuration: BaseConfiguration,
                  patches: GamePatches,
                  status_update: Callable[[str], None] | None = None,
                  ) -> State | None:
    if status_update is None:
        status_update = _quiet_print

    starting_state, logic = setup_resolver(configuration, patches)
    return await advance_depth(starting_state, logic, status_update)
