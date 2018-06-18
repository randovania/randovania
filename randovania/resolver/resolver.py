from typing import Set, Optional

from randovania.resolver import debug
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import Logic
from randovania.resolver.reach import Reach
from randovania.resolver.state import State


def advance_depth(state: State,
                  logic: Logic) -> Optional[State]:
    if logic.game.victory_condition.satisfied(state.resources):
        return state

    reach = Reach.calculate_reach(logic, state)
    debug.log_new_advance(state, reach)

    for action in reach.satisfiable_actions(state):
        new_state = advance_depth(
            state=state.act_on_node(action, logic.game.resource_database, logic.patches),
            logic=logic)

        # We got a positive result. Send it back up
        if new_state:
            return new_state

    debug.log_rollback(state)
    logic.additional_requirements[state.node] = reach.satisfiable_as_requirement_set
    # print("> Rollback finished.")
    return None


def resolve(difficulty_level: int,
            tricks_enabled: Set[int],
            game: GameDescription,
            patches: GamePatches) -> Optional[State]:

    logic, starting_state = logic_bootstrap(difficulty_level, game, patches, tricks_enabled)
    return advance_depth(starting_state, logic)


