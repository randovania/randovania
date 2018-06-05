from typing import List, Set

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription
from randovania.resolver.logic import build_static_resources, calculate_starting_state, calculate_reach, \
    calculate_interesting_resources, uncollected_resource_nodes
from randovania.resolver.resolver import simplify_connections


def generate_list(
        difficulty_level: int,
        tricks_enabled: Set[int],
        item_loss: bool,
        game: GameDescription) -> List[int]:
    # global state for easy printing functions
    debug._gd = game

    static_resources = build_static_resources(difficulty_level, tricks_enabled, game)
    simplify_connections(game, static_resources)
    starting_state = calculate_starting_state(item_loss, game)
    simplify_connections(game, starting_state.resources)

    state = starting_state
    entries = [None] * 128

    while True:
        reach, satisfiable_requirements = calculate_reach(state, game)
        interesting_resources = calculate_interesting_resources(satisfiable_requirements, state.resources)
        potential_pickups = pickups_that_provides_a_resource(pickup_pool, interesting_resources)

        if not potential_pickups:
            raise RuntimeError("BOOM! We don't have any potential pickup. What do we do?")

        # TODO: how do we handle the events?

        potential_locations = uncollected_resource_nodes(reach, state, game)
        location = select_random_element(potential_locations)

        break

    return entries
