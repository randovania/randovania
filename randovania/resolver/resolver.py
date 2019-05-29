from typing import Optional, Tuple, Callable, FrozenSet

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import PickupNode, ResourceNode
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver import debug, event_pickup
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList, state: State,
                               dangerous_resources: FrozenSet[SimpleResourceInfo],
                               ) -> Optional[RequirementList]:
    items = []
    for item in self.values():
        if item.negate:
            return None

        if item.satisfied(state.resources, state.energy):
            continue

        if item.resource.resource_type.is_usable_for_requirement and item.resource not in dangerous_resources:
            # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
            items.append(item)

    return RequirementList(self.difficulty_level, items)


def _simplify_additional_requirement_set(requirements: RequirementSet,
                                         state: State,
                                         dangerous_resources: FrozenSet[SimpleResourceInfo],
                                         ) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state, dangerous_resources)
        for alternative in requirements.alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def _should_check_if_action_is_safe(state: State, action: ResourceNode) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :return:
    """
    if isinstance(action, PickupNode):
        pickup = state.patches.pickup_assignment.get(action.pickup_index)
        if pickup is not None and pickup.item_category.is_major_category:
            return True
    return False


def _inner_advance_depth(state: State,
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

    if logic.game.victory_condition.satisfied(state.resources, state.energy):
        return state, True

    if reach is None:
        reach = ResolverReach.calculate_reach(logic, state)

    debug.log_new_advance(state, reach)
    status_update("Resolving... {} total resources".format(len(state.resources)))

    for action, energy in reach.possible_actions(state):
        if _should_check_if_action_is_safe(state, action):

            potential_state = state.act_on_node(action, path=reach.path_to_node[action], new_energy=energy)
            potential_reach = ResolverReach.calculate_reach(logic, potential_state)

            # If we can go back to where we were, it's a simple safe node
            if state.node in potential_reach.nodes:
                new_result = _inner_advance_depth(state=potential_state,
                                                  logic=logic,
                                                  status_update=status_update,
                                                  reach=potential_reach)

                if not new_result[1]:
                    debug.log_rollback(state, True)

                # If a safe node was a dead end, we're certainly a dead end as well
                return new_result

    has_action = False
    for action, energy in reach.satisfiable_actions(state):
        new_result = _inner_advance_depth(
            state=state.act_on_node(action, path=reach.path_to_node[action], new_energy=energy),
            logic=logic,
            status_update=status_update)

        # We got a positive result. Send it back up
        if new_result[0] is not None:
            return new_result
        else:
            has_action = True

    debug.log_rollback(state, has_action)
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


def advance_depth(state: State, logic: Logic, status_update: Callable[[str], None]) -> Optional[State]:
    return _inner_advance_depth(state, logic, status_update)[0]


def _quiet_print(s):
    pass


def resolve(configuration: LayoutConfiguration,
            game: GameDescription,
            patches: GamePatches,
            status_update: Optional[Callable[[str], None]] = None
            ) -> Optional[State]:
    if status_update is None:
        status_update = _quiet_print

    event_pickup.replace_with_event_pickups(game)

    new_game, starting_state = logic_bootstrap(configuration, game, patches)
    logic = Logic(new_game, configuration)
    starting_state.resources["add_self_as_requirement_to_resources"] = 1
    debug.log_resolve_start()

    return advance_depth(starting_state, logic, status_update)
