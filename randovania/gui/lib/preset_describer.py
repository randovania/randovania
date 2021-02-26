import copy
from typing import List, Iterable, Tuple, Dict

from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pool_creator
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.echoes_configuration import LayoutSkyTempleKeyMode, EchoesConfiguration
from randovania.layout.elevators import LayoutElevators
from randovania.layout.major_item_state import MajorItemState
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.layout.pickup_model import PickupModelStyle
from randovania.layout.preset import Preset
from randovania.layout.prime_configuration import PrimeConfiguration


def _bool_to_str(b: bool) -> str:
    if b:
        return "Yes"
    else:
        return "No"


_ECHOES_TEMPLATE_STRINGS = {
    "Item Placement": [
        "Trick Level: {trick_level}",
        "Randomization Mode: {randomization_mode}",
        "Random Starting Items: {random_starting_items}",
    ],
    "Items": [
        "Starting Items: {starting_items}",
        "Item Pool: {item_pool}",
        "Item Pool Size: {item_pool_size}",
    ],
    "Gameplay": [
        "Starting Location: {starting_location}",
        "Translator Gates: {translator_gates}",
    ],
    "Difficulty": [
        "Damage Strictness: {damage_strictness}",
    ],
    "Game Changes": [
    ],
}
_CORRUPTION_TEMPLATE_STRINGS = {
    "Item Placement": [
        "Trick Level: {trick_level}",
        "Randomization Mode: {randomization_mode}",
        "Random Starting Items: {random_starting_items}",
    ],
    "Items": [
        "Progressive Missile: {progressive_missile}",
        "Progressive Beam: {progressive_beam}",
        "Starting Items: {starting_items}",
        "Item Pool: {item_pool}",
        "Item Pool Size: {item_pool_size}",
    ],
    "Gameplay": [
        "Starting Location: {starting_location}",
        "Teleporters: {elevators}",
    ],
    "Game Changes": [
        "Missiles needs Launcher: {missile_launcher_required}",
        "Ship Missile needs Launcher: {ship_launcher_required}",
        "Final bosses included? {include_final_bosses}",
    ],
    "Difficulty": [
        "Energy Tank: {energy_tank}",
        "1 HP Mode: {dangerous_energy_tank}",
        "Damage Strictness: {damage_strictness}",
        "Pickup Model: {pickup_model}",
    ],
}

_PRIME_TEMPLATE_STRINGS = {
    "Item Placement": [
        "Trick Level: {trick_level}",
        "Randomization Mode: {randomization_mode}",
        "Random Starting Items: {random_starting_items}",
    ],
    "Items": [
        "Starting Items: {starting_items}",
        "Item Pool: {item_pool}",
        "Item Pool Size: {item_pool_size}",
    ],
    "Gameplay": [
        "Starting Location: {starting_location}",
        "Elevators: {elevators}",
    ],
    "Game Changes": [
        "Missiles needs Launcher: {missile_launcher_required}",
        "Power Bomb needs Main: {main_pb_required}",
        "Final bosses included? {include_final_bosses}",
    ],
    "Difficulty": [
        "Energy Tank: {energy_tank}",
        "Damage Strictness: {damage_strictness}",
        "Pickup Model: {pickup_model}",
    ],
}
_EXPECTED_ITEMS = {
    RandovaniaGame.PRIME1: {
        "Scan Visor",
        "Power Beam"
    },
    RandovaniaGame.PRIME2: {
        "Combat Visor",
        "Scan Visor",
        "Morph Ball",
        "Power Beam",
        "Charge Beam",
    },
    RandovaniaGame.PRIME3: {
        "Scan Visor",
        "Morph Ball",
        "Morph Ball Bombs",
        "Power Beam",
        "Charge Beam",
        "Space Jump Boots",
    },
}
_CUSTOM_ITEMS = {
    "Cannon Ball",
}

PresetDescription = Tuple[str, List[str]]


def has_shuffled_item(configuration: MajorItemsConfiguration, item_name: str) -> bool:
    for item, state in configuration.items_state.items():
        if item.name == item_name:
            return state.num_shuffled_pickups > 0
    return False


def _calculate_starting_items(game: RandovaniaGame, items_state: Dict[MajorItem, MajorItemState]) -> str:
    expected_items = _EXPECTED_ITEMS[game]
    starting_items = []

    for major_item, item_state in items_state.items():
        if major_item.required:
            continue

        count = item_state.num_included_in_starting_items
        if count > 0:
            if major_item.name in expected_items:
                continue
            if count > 1:
                starting_items.append(f"{count} {major_item.name}")
            else:
                starting_items.append(major_item.name)

        elif major_item.name in expected_items:
            starting_items.append(f"No {major_item.name}")

    if starting_items:
        return ", ".join(starting_items)
    else:
        # If an expected item is missing, it's added as "No X". So empty starting_items means it's precisely vanilla
        return "Vanilla"


def _calculate_item_pool(game: RandovaniaGame, configuration: MajorItemsConfiguration) -> str:
    item_pool = []

    unexpected_items = _EXPECTED_ITEMS[game] | _CUSTOM_ITEMS
    if game == RandovaniaGame.PRIME2:
        if has_shuffled_item(configuration, "Progressive Grapple"):
            unexpected_items.add("Grapple Beam")
            unexpected_items.add("Screw Attack")
        else:
            unexpected_items.add("Progressive Grapple")

        if has_shuffled_item(configuration, "Progressive Suit"):
            unexpected_items.add("Dark Suit")
            unexpected_items.add("Light Suit")
        else:
            unexpected_items.add("Progressive Suit")

    elif game == RandovaniaGame.PRIME3:
        if has_shuffled_item(configuration, "Progressive Beam"):
            unexpected_items.add("Plasma Beam")
            unexpected_items.add("Nova Beam")
        else:
            unexpected_items.add("Progressive Beam")

        if has_shuffled_item(configuration, "Progressive Missile"):
            unexpected_items.add("Ice Missile")
            unexpected_items.add("Seeker Missile")
        else:
            unexpected_items.add("Progressive Missile")

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


def _format_params_base(configuration: BaseConfiguration) -> dict:
    game_description = default_database.game_description_for(configuration.game)
    major_items = configuration.major_items_configuration

    format_params = {}

    # Item Placement
    random_starting_items = "{} to {}".format(
        major_items.minimum_random_starting_items,
        major_items.maximum_random_starting_items,
    )
    if random_starting_items == "0 to 0":
        random_starting_items = "None"

    format_params["trick_level"] = configuration.trick_level.pretty_description
    format_params["randomization_mode"] = configuration.available_locations.randomization_mode.value
    format_params["random_starting_items"] = random_starting_items

    # Items
    format_params["starting_items"] = _calculate_starting_items(configuration.game, major_items.items_state)
    format_params["item_pool"] = _calculate_item_pool(configuration.game, major_items)
    format_params["item_pool_size"] = "{} of {}".format(*pool_creator.calculate_pool_item_count(configuration))

    # Difficulty
    format_params["damage_strictness"] = configuration.damage_strictness.long_name

    pickup_model = configuration.pickup_model_style.long_name
    if configuration.pickup_model_style != PickupModelStyle.ALL_VISIBLE:
        pickup_model += f" ({configuration.pickup_model_data_source.long_name})"
    format_params["pickup_model"] = pickup_model

    # Gameplay
    starting_locations = configuration.starting_location.locations

    if len(starting_locations) == 1:
        area = game_description.world_list.area_by_area_location(next(iter(starting_locations)))
        format_params["starting_location"] = game_description.world_list.area_name(area)
    else:
        format_params["starting_location"] = "{} locations".format(len(starting_locations))

    return format_params


def _echoes_format_params(configuration: EchoesConfiguration) -> Tuple[Dict[str, List[str]], dict]:
    major_items = configuration.major_items_configuration
    item_database = default_database.item_database_for_game(configuration.game)
    template_strings = copy.deepcopy(_ECHOES_TEMPLATE_STRINGS)

    format_params = {}

    # Items
    inventory_changes = []
    if has_shuffled_item(major_items, "Progressive Suit"):
        inventory_changes.append("Progressive Suit")
    if has_shuffled_item(major_items, "Progressive Grapple"):
        inventory_changes.append("Progressive Grapple")

    unified_ammo = configuration.ammo_configuration.items_state[item_database.ammo["Beam Ammo Expansion"]]
    if unified_ammo.pickup_count == 0:
        inventory_changes.append("Split beam ammo")

    if inventory_changes:
        template_strings["Items"].append(", ".join(inventory_changes))

    # Difficulty
    if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (6, 1.2):
        template_strings["Difficulty"].append("Dark Aether: {:.2f} dmg/s Varia, {:.2f} dmg/s Dark".format(
            configuration.varia_suit_damage, configuration.dark_suit_damage
        ))

    if configuration.energy_per_tank != 100:
        template_strings["Difficulty"].append(f"Energy Tank: {configuration.energy_per_tank} energy")

    if configuration.safe_zone.heal_per_second != 1:
        template_strings["Difficulty"].append(f"Safe Zone: {configuration.safe_zone.heal_per_second:.2f} energy/s")

    if configuration.dangerous_energy_tank:
        template_strings["Difficulty"].append("1-HP Mode")

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

    format_params["translator_gates"] = translator_gates
    format_params["hints"] = "Yes"

    if configuration.elevators != LayoutElevators.VANILLA:
        template_strings["Gameplay"].append(f"Elevators: {configuration.elevators.long_name}")

    # Game Changes
    missile_launcher_required = True
    main_pb_required = True
    for ammo, state in configuration.ammo_configuration.items_state.items():
        if ammo.name == "Missile Expansion":
            missile_launcher_required = state.requires_major_item
        elif ammo.name == "Power Bomb Expansion":
            main_pb_required = state.requires_major_item

    required_messages = []
    if missile_launcher_required:
        required_messages.append("Missiles needs Launcher")
    if main_pb_required:
        required_messages.append("Power Bomb needs Main")

    if required_messages:
        template_strings["Game Changes"].append(", ".join(required_messages))

    qol_changes = []
    if configuration.warp_to_start:
        qol_changes.append("Can warp to start")
    if configuration.menu_mod:
        qol_changes.append("Menu Mod included")
    if configuration.skip_final_bosses:
        qol_changes.append("Final bosses removed")

    if qol_changes:
        template_strings["Game Changes"].append(", ".join(qol_changes))

    if not template_strings["Game Changes"]:
        template_strings.pop("Game Changes")

    # Sky Temple Keys
    if configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
        template_strings["Items"].append("Sky Temple Keys at all bosses")
    elif configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        template_strings["Items"].append("Sky Temple Keys at all guardians")
    else:
        template_strings["Items"].append(f"{configuration.sky_temple_keys.num_keys} Sky Temple Keys shuffled")

    # Item Model
    if configuration.pickup_model_style != PickupModelStyle.ALL_VISIBLE:
        template_strings["Difficulty"].append(f"Pickup: {configuration.pickup_model_style.long_name} "
                                              f"({configuration.pickup_model_data_source.long_name})")

    return template_strings, format_params


def _corruption_format_params(configuration: CorruptionConfiguration) -> dict:
    major_items = configuration.major_items_configuration

    format_params = {"energy_tank": f"{configuration.energy_per_tank} energy",
                     "dangerous_energy_tank": _bool_to_str(configuration.dangerous_energy_tank),
                     "include_final_bosses": _bool_to_str(not configuration.skip_final_bosses),
                     "elevators": configuration.elevators.value,
                     "progressive_missile": _bool_to_str(has_shuffled_item(major_items, "Progressive Missile")),
                     "progressive_beam": _bool_to_str(has_shuffled_item(major_items, "Progressive Beam"))}

    missile_launcher_required = True
    ship_launcher_required = True
    for ammo, state in configuration.ammo_configuration.items_state.items():
        if ammo.name == "Missile Expansion":
            missile_launcher_required = state.requires_major_item
        elif ammo.name == "Ship Missile Expansion":
            ship_launcher_required = state.requires_major_item

    format_params["missile_launcher_required"] = _bool_to_str(missile_launcher_required)
    format_params["ship_launcher_required"] = _bool_to_str(ship_launcher_required)

    return format_params


def _prime_format_params(configuration: PrimeConfiguration) -> dict:
    major_items = configuration.major_items_configuration

    format_params = {"energy_tank": f"{configuration.energy_per_tank} energy",
                     "dangerous_energy_tank": _bool_to_str(configuration.dangerous_energy_tank),
                     "include_final_bosses": _bool_to_str(not configuration.skip_final_bosses),
                     "elevators": configuration.elevators.value
                     }

    missile_launcher_required = True
    main_pb_required = True
    for ammo, state in configuration.ammo_configuration.items_state.items():
        if ammo.name == "Missile Expansion":
            missile_launcher_required = state.requires_major_item
        elif ammo.name == "Power Bomb Expansion":
            main_pb_required = state.requires_major_item

    format_params["missile_launcher_required"] = _bool_to_str(missile_launcher_required)
    format_params["main_pb_required"] = _bool_to_str(main_pb_required)

    return format_params


def describe(preset: Preset) -> Iterable[PresetDescription]:
    configuration = preset.configuration

    format_params = _format_params_base(configuration)

    template_strings = None
    if preset.game == RandovaniaGame.PRIME2:
        template_strings, params = _echoes_format_params(configuration)
        format_params.update(params)

    elif preset.game == RandovaniaGame.PRIME3:
        template_strings = _CORRUPTION_TEMPLATE_STRINGS
        format_params.update(_corruption_format_params(configuration))

    elif preset.game == RandovaniaGame.PRIME1:
        template_strings = _PRIME_TEMPLATE_STRINGS
        format_params.update(_prime_format_params(configuration))

    for category, templates in template_strings.items():
        yield category, [
            item.format(**format_params)
            for item in templates
        ]


def merge_categories(categories: Iterable[PresetDescription]) -> str:
    return "".join(
        """<h4><span style="font-weight:600;">{}</span></h4><p>{}</p>""".format(category, "<br />".join(items))
        for category, items in categories
    )
