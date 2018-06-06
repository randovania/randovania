from typing import Set, Optional

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription, RequirementSet
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import build_static_resources, \
    Logic
from randovania.resolver.reach import Reach
from randovania.resolver.resources import CurrentResources
from randovania.resolver.state import State


def advance_depth(state: State,
                  logic: Logic) -> Optional[State]:
    if logic.game.victory_condition.satisfied(state.resources):
        return state

    reach = Reach.calculate_reach(state)
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


def simplify_connections(game: GameDescription, resources: CurrentResources) -> None:
    for world in game.worlds:
        for area in world.areas:
            for connections in area.connections.values():
                for target, value in connections.items():
                    connections[target] = value.simplify(resources, game.resource_database)


def resolve(difficulty_level: int,
            tricks_enabled: Set[int],
            item_loss: bool,
            game: GameDescription,
            patches: GamePatches) -> Optional[State]:
    # global state for easy printing functions
    debug._gd = game

    logic = Logic(game, patches)
    starting_state = State.calculate_starting_state(item_loss, logic)

    simplify_connections(game,
                         build_static_resources(difficulty_level, tricks_enabled, game))
    simplify_connections(game, starting_state.resources)

    return advance_depth(starting_state, logic)
