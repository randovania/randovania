from typing import Set, Optional

from randovania.resolver import debug
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.logic import Logic
from randovania.resolver.reach import Reach
from randovania.resolver.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.resolver.resources import PickupIndex
from randovania.resolver.state import State


def _simplify_requirement_list(self: RequirementList) -> Optional[RequirementList]:
    items = []
    for item in self:  # type: IndividualRequirement
        if item.negate:
            return None

        if not isinstance(item.resource, PickupIndex):
            # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
            items.append(item)

    return RequirementList(items)


def _simplify_requirement_set_for_additional_requirements(requirements: RequirementSet) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative)
        for alternative in requirements.alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def advance_depth(state: State,
                  logic: Logic) -> Optional[State]:
    if logic.game.victory_condition.satisfied(state.resources, state.resource_database):
        return state

    reach = Reach.calculate_reach(logic, state)
    debug.log_new_advance(state, reach, logic)

    for action in reach.satisfiable_actions(state):
        new_state = advance_depth(
            state=state.act_on_node(action,
                                    logic.patches.pickup_mapping,
                                    path=reach.path_to_node[action]
                                    ),
            logic=logic)

        # We got a positive result. Send it back up
        if new_state:
            return new_state

    debug.log_rollback(state)
    logic.additional_requirements[state.node] = _simplify_requirement_set_for_additional_requirements(
        reach.satisfiable_as_requirement_set)
    return None


def resolve(difficulty_level: int,
            tricks_enabled: Set[int],
            configuration: LayoutConfiguration,
            game: GameDescription,
            patches: GamePatches) -> Optional[State]:

    logic, starting_state = logic_bootstrap(difficulty_level, configuration, game, patches, tricks_enabled)
    debug.log_resolve_start()
    return advance_depth(starting_state, logic)


