import copy
from typing import Tuple, Set

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.logic import Logic, build_static_resources
from randovania.resolver.resources import merge_resources
from randovania.resolver.state import State


def logic_bootstrap(difficulty_level: int,
                    configuration: LayoutConfiguration,
                    game: GameDescription,
                    patches: GamePatches,
                    tricks_enabled: Set[int]) -> Tuple[Logic, State]:
    """
    Core code for starting a new Logic/State.
    :param difficulty_level:
    :param game:
    :param patches:
    :param tricks_enabled:
    :return:
    """

    # global state for easy printing functions
    debug._gd = game

    game = copy.deepcopy(game)
    logic = Logic(game, configuration, patches)
    starting_state = State.calculate_starting_state(logic)

    game.simplify_connections(merge_resources(
        build_static_resources(difficulty_level, tricks_enabled, game.resource_database),
        starting_state.resources))

    return logic, starting_state
