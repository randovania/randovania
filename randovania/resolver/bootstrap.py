import copy
from typing import Tuple, Set

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import merge_resources, ResourceDatabase, CurrentResources
from randovania.resolver import debug
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutLogic
from randovania.resolver.logic import Logic
from randovania.resolver.state import State

_items_to_not_add_in_minimal_restrictions = {
    # Dark Visor
    10,

    # Light Suit
    14,

    # Screw Attack
    27,

    # Sky Temple Keys
    29, 30, 31, 101, 102, 103, 104, 105, 106
}

_minimal_restrictions_custom_item_count = {
    # Energy Tank
    42: 14,
    # Power Bomb
    43: 10,
    # Missile
    44: 100,
    # Dark Ammo
    45: 100,
    # Light Ammo
    46: 100
}


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
        # 14,  # Controller Reset
        15,  # Instant Morph
    }

    # Skipping Controller Reset and Exclude from Room Randomizer

    if logic == LayoutLogic.NO_GLITCHES:
        return 0, set()
    elif logic == LayoutLogic.TRIVIAL:
        return 1, set()
    elif logic == LayoutLogic.EASY:
        return 2, tricks
    elif logic == LayoutLogic.NORMAL:
        return 3, tricks
    elif logic == LayoutLogic.HARD:
        return 4, tricks
    elif logic == LayoutLogic.HYPERMODE or logic == LayoutLogic.MINIMAL_RESTRICTIONS:
        return 5, tricks
    else:
        raise RuntimeError("Unsupported logic")


def static_resources_for_layout_logic(
        layout_logic: LayoutLogic,
        resource_database: ResourceDatabase,
) -> Tuple[int, CurrentResources]:
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

    return difficulty_level, static_resources


def _add_minimal_restrictions_initial_resources(resources: CurrentResources,
                                                resource_database: ResourceDatabase,
                                                ) -> None:
    # TODO: this function assumes we're talking about Echoes
    for event in resource_database.event:
        # Ignoring Emperor Ing event, otherwise we're done automatically
        if event.index != 8:
            resources[event] = 1

    for item in resource_database.item:
        if item.index not in _items_to_not_add_in_minimal_restrictions:
            resources[item] = _minimal_restrictions_custom_item_count.get(item.index, 1)


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

    if configuration.logic == LayoutLogic.MINIMAL_RESTRICTIONS:
        _add_minimal_restrictions_initial_resources(starting_state.resources,
                                                    game.resource_database)

    difficulty_level, static_resources = static_resources_for_layout_logic(configuration.logic, game.resource_database)

    starting_state.resources = merge_resources(static_resources, starting_state.resources)
    game.simplify_connections(starting_state.resources)

    starting_state.resources[game.resource_database.difficulty_resource] = difficulty_level

    return logic, starting_state
