from typing import List, Dict, Iterable, Tuple

from randovania.game_description import data_reader
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.preset import Preset

_TEMPLATE_STRINGS = {
    "Item Placement": [
        "Trick Level: {trick_level}",
        "Randomization Mode: {randomization_mode}",
        "Random Starting Items: {random_starting_items}",
    ],
    "Items": [
        "Progressive Suit: {progressive_suit}",
        "Progressive Grapple: {progressive_grapple}",
        "Split Beam Ammo: {split_beam_ammo}",
        "Starting Items: {starting_items}",
        "Custom Items: {custom_items}",
    ],
    "Gameplay": [
        "Starting Location: {starting_location}",
        "Translator Gates: {translator_gates}",
        "Elevators: {elevators}",
        # "Hints: {hints}",
    ],
    "Game Changes": [
        "Missiles needs Launcher: {missile_launcher_required}",
        "Power Bombs needs Main PBs: {main_pb_required}",
        "Warp to Start: {warp_to_start}",
        # "Quality of Life Improvements: {generic_patches}",
    ],
    "Difficulty": [
        "Dark Aether Suit Damage: {dark_aether_suit_damage}",
        "Dark Aether Damage Strictness: {dark_aether_damage_strictness}",
        "Pickup Model: {pickup_model}",
    ],
    "Sky Temple Keys": [
        "Target: {target}",
        # "Location: {location}",
    ],
}

PresetDescription = Tuple[str, List[str]]


def describe(preset: Preset) -> Iterable[PresetDescription]:
    patcher = preset.patcher_configuration
    configuration = preset.layout_configuration
    major_items = configuration.major_items_configuration

    game_description = data_reader.decode_data(preset.layout_configuration.game_data)

    format_params = {}

    def _bool_to_str(b: bool) -> str:
        if b:
            return "Yes"
        else:
            return "No"

    # Item Placement

    random_starting_items = "{} to {}".format(
        major_items.minimum_random_starting_items,
        major_items.maximum_random_starting_items,
    )
    if random_starting_items == "0 to 0":
        random_starting_items = "None"

    format_params["trick_level"] = configuration.trick_level_configuration.pretty_description
    format_params["randomization_mode"] = configuration.randomization_mode.value
    format_params["random_starting_items"] = random_starting_items

    # Items
    format_params["progressive_suit"] = _bool_to_str(major_items.progressive_suit)
    format_params["progressive_grapple"] = _bool_to_str(major_items.progressive_grapple)
    format_params["split_beam_ammo"] = _bool_to_str(configuration.split_beam_ammo)
    format_params["starting_items"] = "???"
    format_params["custom_items"] = "None"

    # Difficulty
    default_patcher = PatcherConfiguration()

    if patcher.varia_suit_damage == default_patcher.varia_suit_damage and (
            patcher.dark_suit_damage == default_patcher.dark_suit_damage):
        dark_aether_suit_damage = "Normal"
    else:
        dark_aether_suit_damage = "Custom"

    format_params["dark_aether_suit_damage"] = dark_aether_suit_damage
    format_params["dark_aether_damage_strictness"] = configuration.damage_strictness.long_name
    format_params["pickup_model"] = patcher.pickup_model_style.value

    # Gameplay
    translator_gates = "Custom"
    translator_configurations = [
        (configuration.translator_configuration.with_vanilla_actual(), "Vanilla (Actual)"),
        (configuration.translator_configuration.with_vanilla_colors(), "Vanilla (Colors)"),
        (configuration.translator_configuration.with_full_random(), "Random"),
    ]
    for translator_config, name in translator_configurations:
        if translator_config == configuration.translator_configuration:
            translator_gates = name
            break

    starting_locations = configuration.starting_location.locations

    if len(starting_locations) == 1:
        area = game_description.world_list.area_by_area_location(next(iter(starting_locations)))
        format_params["starting_location"] = game_description.world_list.area_name(area, distinguish_dark_aether=True)
    else:
        format_params["starting_location"] = "{} locations".format(len(starting_locations))

    format_params["translator_gates"] = translator_gates
    format_params["elevators"] = configuration.elevators.value
    format_params["hints"] = "Yes"

    # Game Changes
    missile_launcher_required = True
    main_pb_required = True
    for ammo, state in configuration.ammo_configuration.items_state.items():
        if ammo.name == "Missile Expansion":
            missile_launcher_required = state.requires_major_item
        elif ammo.name == "Power Bomb Expansion":
            main_pb_required = state.requires_major_item

    format_params["missile_launcher_required"] = _bool_to_str(missile_launcher_required)
    format_params["main_pb_required"] = _bool_to_str(main_pb_required)
    format_params["warp_to_start"] = _bool_to_str(patcher.warp_to_start)
    format_params["generic_patches"] = "Some"

    # Sky Temple Keys
    if configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
        stk_location = "Bosses"
    elif configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        stk_location = "Guardians"
    else:
        stk_location = "Random"

    format_params["target"] = "{0} of {0}".format(configuration.sky_temple_keys.num_keys)
    format_params["location"] = stk_location

    for category, templates in _TEMPLATE_STRINGS.items():
        yield category, [
            item.format(**format_params)
            for item in templates
        ]


def merge_categories(categories: Iterable[PresetDescription]) -> str:
    return "".join(
        """<h4><span style="font-weight:600;">{}</span></h4><p>{}</p>""".format(category, "<br />".join(items))
        for category, items in categories
    )
