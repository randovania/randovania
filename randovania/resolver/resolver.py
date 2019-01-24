from typing import Optional, Tuple, Callable

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.game_description.resources import PickupIndex
from randovania.resolver import debug
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList, state: State) -> Optional[RequirementList]:
    items = []
    for item in self.values():
        if item.negate:
            return None

        if item.satisfied(state.resources, state.resource_database):
            continue

        if not isinstance(item.resource, PickupIndex):
            # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
            items.append(item)

    return RequirementList(self.difficulty_level, items)


def _simplify_requirement_set_for_additional_requirements(requirements: RequirementSet,
                                                          state: State) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state)
        for alternative in requirements.alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def _inner_advance_depth(state: State,
                         logic: Logic,
                         status_update: Callable[[str], None],
                         ) -> Tuple[Optional[State], bool]:

    if logic.game.victory_condition.satisfied(state.resources, state.resource_database):
        return state, True

    reach = ResolverReach.calculate_reach(logic, state)
    debug.log_new_advance(state, reach)
    status_update("Resolving... {} total resources".format(len(state.resources)))

    has_action = False
    for action in reach.satisfiable_actions(state):
        new_result = _inner_advance_depth(
            state=state.act_on_node(action, path=reach.path_to_node[action]),
            logic=logic,
            status_update=status_update)

        # We got a positive result. Send it back up
        if new_result[0] is not None:
            return new_result
        else:
            has_action = True

    debug.log_rollback(state, has_action)
    if not has_action:
        logic.additional_requirements[state.node] = _simplify_requirement_set_for_additional_requirements(
            reach.satisfiable_as_requirement_set, state)

    return None, has_action


def advance_depth(state: State, logic: Logic, status_update: Callable[[str], None]) -> Optional[State]:
    return _inner_advance_depth(state, logic, status_update)[0]


def resolve(configuration: LayoutConfiguration,
            game: GameDescription,
            patches: GamePatches,
            status_update: Optional[Callable[[str], None]] = None
            ) -> Optional[State]:
    if status_update is None:
        status_update = lambda s: None

    logic, starting_state = logic_bootstrap(configuration, game, patches)
    debug.log_resolve_start()
    return advance_depth(starting_state, logic, status_update)
