import asyncio
from typing import Callable

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.event_pickup import EventPickupNode
from randovania.game_description.world.node import Node
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.resource_node import ResourceNode
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver import debug
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList, state: State,
                               dangerous_resources: frozenset[ResourceInfo],
                               ) -> RequirementList | None:
    items = []
    for item in self.values():
        if item.negate:
            return None

        if item.satisfied(state.resources, state.energy, state.resource_database):
            continue

        if item.resource not in dangerous_resources:
            # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
            items.append(item)

    return RequirementList(items)


def _simplify_additional_requirement_set(requirements: RequirementSet,
                                         state: State,
                                         dangerous_resources: frozenset[ResourceInfo],
                                         ) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state, dangerous_resources)
        for alternative in requirements.alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def _should_check_if_action_is_safe(state: State,
                                    action: ResourceNode,
                                    dangerous_resources: frozenset[ResourceInfo],
                                    all_nodes: tuple[Node, ...]) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :return:
    """
    if any(resource in dangerous_resources
           for resource in action.resource_gain_on_collect(state.node_context())):
        return False

    if isinstance(action, EventNode):
        return True

    if isinstance(action, EventPickupNode):
        pickup_node = action.pickup_node
    else:
        pickup_node = action

    if isinstance(pickup_node, PickupNode):
        target = state.patches.pickup_assignment.get(pickup_node.pickup_index)
        if target is not None and (target.pickup.item_category.is_major or target.pickup.item_category.is_key):
            return True

    return False


class ResolverTimeout(Exception):
    pass


attempts = 0


def set_attempts(value: int):
    global attempts
    attempts = value


def get_attempts() -> int:
    global attempts
    return attempts


def _check_attempts(max_attempts: int | None):
    global attempts
    if max_attempts is not None and attempts >= max_attempts:
        raise ResolverTimeout(f"Timed out after {max_attempts} attempts")
    attempts += 1


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

    _check_attempts(max_attempts)
    debug.log_new_advance(state, reach)
    status_update(f"Resolving... {state.resources.num_resources} total resources")

    for action, energy in reach.possible_actions(state):
        if _should_check_if_action_is_safe(state, action, logic.game.dangerous_resources,
                                           logic.game.world_list.iterate_nodes()):
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

                if not new_result[1]:
                    debug.log_rollback(state, True, True)

                # If a safe node was a dead end, we're certainly a dead end as well
                return new_result

    debug.log_checking_satisfiable_actions()
    has_action = False
    for action, energy in reach.satisfiable_actions(state, logic.victory_condition):
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

    debug.log_rollback(state, has_action, False)
    additional_requirements = reach.satisfiable_as_requirement_set

    if has_action:
        additional = set()
        for resource_node in reach.collectable_resource_nodes(state):
            additional |= logic.get_additional_requirements(resource_node).alternatives

        additional_requirements = additional_requirements.union(RequirementSet(additional))

    logic.set_additional_requirements(
        state.node,
        _simplify_additional_requirement_set(additional_requirements,
                                             state,
                                             logic.game.dangerous_resources)
    )
    return None, has_action


async def advance_depth(state: State, logic: Logic, status_update: Callable[[str], None],
                        max_attempts: int | None = None) -> State | None:
    return (await _inner_advance_depth(state, logic, status_update, max_attempts=max_attempts))[0]


def _quiet_print(s):
    pass


def setup_resolver(configuration: BaseConfiguration, patches: GamePatches) -> tuple[State, Logic]:
    set_attempts(0)

    game = filtered_database.game_description_for_layout(configuration).get_mutable()
    bootstrap = game.game.generator.bootstrap

    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)

    new_game, starting_state = bootstrap.logic_bootstrap(configuration, game, patches)
    logic = Logic(new_game, configuration)
    starting_state.resources.add_self_as_requirement_to_resources = True

    return starting_state, logic


async def resolve(configuration: BaseConfiguration,
                  patches: GamePatches,
                  status_update: Callable[[str], None] | None = None
                  ) -> State | None:
    if status_update is None:
        status_update = _quiet_print

    starting_state, logic = setup_resolver(configuration, patches)
    debug.log_resolve_start()

    return await advance_depth(starting_state, logic, status_update)
