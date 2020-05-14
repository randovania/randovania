import copy
from typing import List, Iterable, Tuple, Dict

from randovania.game_description import data_reader
from randovania.game_description.item.major_item import MajorItem
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.major_items_configuration import MajorItemsConfiguration
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
        "Item Pool: {item_pool}",
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
        "Final bosses included? {include_final_bosses}",
        "Menu Mod included? {menu_mod}",
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
_EXPECTED_ITEMS = {
    "Scan Visor",
    "Morph Ball",
    "Power Beam",
    "Charge Beam",
}
_CUSTOM_ITEMS = {
    "Cannon Ball",
}

PresetDescription = Tuple[str, List[str]]


def _calculate_starting_items(items_state: Dict[MajorItem, MajorItemState]) -> str:
    starting_items = []
    for major_item, item_state in items_state.items():
        if major_item.required:
            continue

        count = item_state.num_included_in_starting_items
        if count > 0:
            if major_item.name in _EXPECTED_ITEMS:
                continue
            if count > 1:
                starting_items.append(f"{count} {major_item.name}")
            else:
                starting_items.append(major_item.name)

        elif major_item.name in _EXPECTED_ITEMS:
            starting_items.append(f"No {major_item.name}")

    if starting_items:
        return ", ".join(starting_items)
    else:
        # If an expected item is missing, it's added as "No X". So empty starting_items means it's precisely vanilla
        return "Vanilla"


def _calculate_item_pool(configuration: MajorItemsConfiguration) -> str:
    item_pool = []

    unexpected_items = _EXPECTED_ITEMS | _CUSTOM_ITEMS
    if configuration.progressive_grapple:
        unexpected_items.add("Grapple Beam")
        unexpected_items.add("Screw Attack")
    else:
        unexpected_items.add("Progressive Grapple")

    if configuration.progressive_suit:
        unexpected_items.add("Dark Suit")
        unexpected_items.add("Light Suit")
    else:
        unexpected_items.add("Progressive Suit")

    for major_item, item_state in configuration.items_state.items():
        if major_item.required:
            continue

        item_was_expected = major_item.name not in unexpected_items

        if item_state.num_shuffled_pickups > 0 or item_state.include_copy_in_original_location:
            item_in_pool = True
        else:
            item_in_pool = False

        if item_in_pool:
            if not item_was_expected:
                item_pool.append(major_item.name)
        else:
            if item_was_expected and item_state.num_included_in_starting_items == 0:
                item_pool.append(f"No {major_item.name}")

    if item_pool:
        return ", ".join(item_pool)
    else:
        return "Default"


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
    format_params["starting_items"] = _calculate_starting_items(configuration.major_items_configuration.items_state)
    format_params["item_pool"] = _calculate_item_pool(configuration.major_items_configuration)

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
    format_params["menu_mod"] = _bool_to_str(patcher.menu_mod)
    format_params["include_final_bosses"] = _bool_to_str(not configuration.skip_final_bosses)

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
