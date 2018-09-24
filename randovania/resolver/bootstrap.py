import copy
from typing import Tuple, Set

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic
from randovania.resolver.logic import Logic
from randovania.resolver.resources import merge_resources, ResourceDatabase, CurrentResources
from randovania.resolver.state import State


def expand_layout_logic(logic: LayoutLogic) -> Tuple[int, Set[int]]:
    """

    :param logic:
    :return:
    """
    tricks = {
        0,  # Scan Dash
        1,  # Difficult Bomb Jump
        2,  # Slope Jump
        3,  # R Jump
        4,  # BSJ
        5,  # Roll Jump
        6,  # Underwater Dash
        7,  # Air Underwater
        8,  # Floaty
        9,  # Infinite Speed
        10,  # SA without SJ
        11,  # Wall Boost
        12,  # Jump off Enemy
        14,  # Controller Reset
        15,  # Instant Morph
    }

    # Skipping Controller Reset and Exclude from Room Randomizer

    if logic == LayoutLogic.NO_GLITCHES:
        return 0, set()
    elif logic == LayoutLogic.EASY:
        return 2, tricks
    elif logic == LayoutLogic.NORMAL:
        return 3, tricks
    elif logic == LayoutLogic.HARD:
        return 5, tricks
    else:
        raise RuntimeError("Unsupported logic")


def static_resources_for_layout_logic(
        layout_logic: LayoutLogic,
        resource_database: ResourceDatabase,
        ) -> CurrentResources:
    """

    :param layout_logic:
    :param resource_database:
    :return:
    """

    static_resources = {}
    difficulty_level, tricks_enabled = expand_layout_logic(layout_logic)

    for trick in resource_database.trick:
        if trick.index in tricks_enabled:
            static_resources[trick] = 1
        else:
            static_resources[trick] = 0

    for difficulty in resource_database.difficulty:
        static_resources[difficulty] = difficulty_level

    return static_resources


def logic_bootstrap(configuration: LayoutConfiguration,
                    game: GameDescription,
                    patches: GamePatches,
                    ) -> Tuple[Logic, State]:
    """
    Core code for starting a new Logic/State.
    :param configuration:
    :param game:
    :param patches:
    :return:
    """

    # global state for easy printing functions
    debug._gd = game

    game = copy.deepcopy(game)
    logic = Logic(game, configuration, patches)
    starting_state = State.calculate_starting_state(logic)

    game.simplify_connections(merge_resources(
        static_resources_for_layout_logic(configuration.logic, game.resource_database),
        starting_state.resources))

    return logic, starting_state
