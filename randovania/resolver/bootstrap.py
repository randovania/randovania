import copy
from typing import Tuple, Set

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase, find_resource_info_with_long_name
from randovania.game_description.resources.resource_info import CurrentResources, \
    add_resource_gain_to_current_resources, add_resources_into_another
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel
from randovania.layout.translator_configuration import TranslatorConfiguration
from randovania.resolver import debug
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

_events_for_vanilla_item_loss_from_ship = {
    2,
    4,
    71,
    78,
}


def expand_layout_logic(logic: LayoutTrickLevel) -> Tuple[int, Set[int]]:
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
        18,  # Exclude from Room Rando
    }

    # Skipping Controller Reset and Exclude from Room Randomizer

    if logic == LayoutTrickLevel.NO_TRICKS:
        return 0, set()
    elif logic == LayoutTrickLevel.TRIVIAL:
        return 1, set()
    elif logic == LayoutTrickLevel.EASY:
        return 2, tricks
    elif logic == LayoutTrickLevel.NORMAL:
        return 3, tricks
    elif logic == LayoutTrickLevel.HARD:
        return 4, tricks
    elif logic == LayoutTrickLevel.HYPERMODE or logic == LayoutTrickLevel.MINIMAL_RESTRICTIONS:
        return 5, tricks
    else:
        raise RuntimeError("Unsupported logic")


def static_resources_for_layout_logic(
        layout_logic: LayoutTrickLevel,
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
        # Ingoring these events:
        # Emperor Ing (8), otherwise we're done automatically
        # Chykka (28), otherwise we can't collect Dark Visor
        if event.index not in {8, 28}:
            resources[event] = 1

    for item in resource_database.item:
        if item.index not in _items_to_not_add_in_minimal_restrictions:
            resources[item] = _minimal_restrictions_custom_item_count.get(item.index, 1)


def calculate_starting_state(logic: Logic, patches: GamePatches) -> "State":
    game = logic.game

    # TODO: is this fast start?
    initial_game_state = game.initial_states["Default"]

    starting_area = game.world_list.area_by_asset_id(patches.starting_location.area_asset_id)

    starting_node = starting_area.nodes[starting_area.default_node_index]

    initial_resources = copy.copy(patches.starting_items)
    initial_resources[game.resource_database.trivial_resource()] = 1

    if initial_game_state is not None:
        add_resource_gain_to_current_resources(initial_game_state, initial_resources)

    starting_state = State(
        initial_resources,
        starting_node,
        patches,
        None,
        game.resource_database
    )

    # Being present with value 0 is troublesome since this dict is used for a simplify_requirements later on
    keys_to_remove = [resource for resource, quantity in initial_resources.items() if quantity == 0]
    for resource in keys_to_remove:
        del initial_resources[resource]

    return starting_state


def _create_vanilla_translator_resources(resource_database: ResourceDatabase,
                                         translator_configuration: TranslatorConfiguration,
                                         ) -> CurrentResources:
    """

    :param resource_database:
    :param translator_configuration:
    :return:
    """
    events = [
        ("Vanilla GFMC Compound Translator Gate", not translator_configuration.fixed_gfmc_compound),
        ("Vanilla Torvus Temple Translator Gate", not translator_configuration.fixed_torvus_temple),
        ("Vanilla Great Temple Emerald Translator Gate", not translator_configuration.fixed_great_temple),
    ]

    return {
        find_resource_info_with_long_name(resource_database.trick, name): 1 if active else 0
        for name, active in events
    }


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
    logic = Logic(game, configuration)
    starting_state = calculate_starting_state(logic, patches)

    if configuration.trick_level == LayoutTrickLevel.MINIMAL_RESTRICTIONS:
        _add_minimal_restrictions_initial_resources(starting_state.resources,
                                                    game.resource_database)

    difficulty_level, static_resources = static_resources_for_layout_logic(configuration.trick_level,
                                                                           game.resource_database)
    add_resources_into_another(starting_state.resources, static_resources)
    add_resources_into_another(starting_state.resources,
                               _create_vanilla_translator_resources(game.resource_database,
                                                                    configuration.translator_configuration))
    starting_state.resources[game.resource_database.difficulty_resource] = difficulty_level

    game.simplify_connections(starting_state.resources)

    return logic, starting_state
