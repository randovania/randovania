from typing import Set, Optional

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription, RequirementSet, CurrentResources
from randovania.resolver.logic import calculate_reach, calculate_satisfiable_actions, build_static_resources, \
    calculate_starting_state
from randovania.resolver.state import State


def advance_depth(state: State, game: GameDescription) -> Optional[State]:
    if game.victory_condition.satisfied(state.resources):
        return state

    reach, satisfiable_requirements = calculate_reach(state, game)
    debug.log_new_advance(state, reach)

    for action in calculate_satisfiable_actions(state, reach, satisfiable_requirements, game):
        new_state = advance_depth(
            state.act_on_node(action, game.resource_database, game.pickup_database), game)
        if new_state:
            return new_state

    debug.log_rollback(state)
    game.additional_requirements[state.node] = RequirementSet(satisfiable_requirements)
    # print("> Rollback finished.")
    return None


def simplify_connections(game: GameDescription, static_resources: CurrentResources) -> None:
    for world in game.worlds:
        for area in world.areas:
            for connections in area.connections.values():
                for target, value in connections.items():
                    connections[target] = value.simplify(static_resources, game.resource_database)


def resolve(difficulty_level: int,
            tricks_enabled: Set[int],
            item_loss: bool,
            game: GameDescription) -> Optional[State]:
    # global state for easy printing functions
    debug._gd = game

    static_resources = build_static_resources(difficulty_level, tricks_enabled, game)
    simplify_connections(game, static_resources)
    starting_state = calculate_starting_state(item_loss, game)
    simplify_connections(game, starting_state.resources)

    return advance_depth(starting_state, game)
