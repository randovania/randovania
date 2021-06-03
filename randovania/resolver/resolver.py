import asyncio
import copy
from typing import Optional, Tuple, Callable, FrozenSet

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node import PickupNode, ResourceNode, EventNode, Node
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.resolver import debug, event_pickup, bootstrap
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.event_pickup import EventPickupNode
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList, state: State,
                               dangerous_resources: FrozenSet[ResourceInfo],
                               ) -> Optional[RequirementList]:
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
                                         dangerous_resources: FrozenSet[ResourceInfo],
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
                                    dangerous_resources: FrozenSet[ResourceInfo],
                                    all_nodes: Tuple[Node, ...]) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :return:
    """
    if any(resource in dangerous_resources
           for resource in action.resource_gain_on_collect(state.patches, state.resources, all_nodes,
                                                           state.resource_database)):
        return False

    if isinstance(action, EventNode):
        return True

    if isinstance(action, EventPickupNode):
        pickup_node = action.pickup_node
    else:
        pickup_node = action

    if isinstance(pickup_node, PickupNode):
        target = state.patches.pickup_assignment.get(pickup_node.pickup_index)
        if target is not None and (target.pickup.item_category.is_major_category or target.pickup.item_category.is_key):
            return True

    return False


async def _inner_advance_depth(state: State,
                               logic: Logic,
                               status_update: Callable[[str], None],
                               *,
                               reach: Optional[ResolverReach] = None,
                               ) -> Tuple[Optional[State], bool]:
    """

    :param state:
    :param logic:
    :param status_update:
    :param reach: A precalculated reach for the given state
    :return:
    """

    if logic.game.victory_condition.satisfied(state.resources, state.energy, state.resource_database):
        return state, True

    # Yield back to the asyncio runner, so cancel can do something
    await asyncio.sleep(0)

    if reach is None:
        reach = ResolverReach.calculate_reach(logic, state)

    debug.log_new_advance(state, reach)
    status_update("Resolving... {} total resources".format(len(state.resources)))

    for action, energy in reach.possible_actions(state):
        if _should_check_if_action_is_safe(state, action, logic.game.dangerous_resources,
                                           logic.game.world_list.all_nodes):

            potential_state = state.act_on_node(action, path=reach.path_to_node[action], new_energy=energy)
            potential_reach = ResolverReach.calculate_reach(logic, potential_state)

            # If we can go back to where we were, it's a simple safe node
            if state.node in potential_reach.nodes:
                new_result = await _inner_advance_depth(
                    state=potential_state,
                    logic=logic,
                    status_update=status_update,
                    reach=potential_reach,
                )

                if not new_result[1]:
                    debug.log_rollback(state, True, True)

                # If a safe node was a dead end, we're certainly a dead end as well
                return new_result

    debug.log_checking_satisfiable_actions()
    has_action = False
    for action, energy in reach.satisfiable_actions(state, logic.game.victory_condition):
        new_result = await _inner_advance_depth(
            state=state.act_on_node(action, path=reach.path_to_node[action], new_energy=energy),
            logic=logic,
            status_update=status_update,
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

    logic.additional_requirements[state.node] = _simplify_additional_requirement_set(additional_requirements,
                                                                                     state,
                                                                                     logic.game.dangerous_resources)
    return None, has_action


async def advance_depth(state: State, logic: Logic, status_update: Callable[[str], None]) -> Optional[State]:
    return (await _inner_advance_depth(state, logic, status_update))[0]


def _quiet_print(s):
    pass


async def resolve(configuration: EchoesConfiguration,
                  patches: GamePatches,
                  status_update: Optional[Callable[[str], None]] = None
                  ) -> Optional[State]:
    if status_update is None:
        status_update = _quiet_print

    game = default_database.game_description_for(configuration.game).make_mutable_copy()
    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)
    event_pickup.replace_with_event_pickups(game)

    new_game, starting_state = bootstrap.logic_bootstrap(configuration, game, patches)
    logic = Logic(new_game, configuration)
    starting_state.resources["add_self_as_requirement_to_resources"] = 1
    debug.log_resolve_start()

    for name, req in new_game.resource_database.requirement_template.items():
        print(name, req)

    return await advance_depth(starting_state, logic, status_update)
