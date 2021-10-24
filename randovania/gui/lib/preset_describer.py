import collections
from typing import List, Iterable, Tuple, Dict

from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import pool_creator
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.major_item_state import MajorItemState
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.preset import Preset
from randovania.layout.prime1.prime_configuration import PrimeConfiguration, LayoutCutsceneMode
from randovania.layout.prime2.echoes_configuration import LayoutSkyTempleKeyMode, EchoesConfiguration
from randovania.layout.prime3.corruption_configuration import CorruptionConfiguration


def _bool_to_str(b: bool) -> str:
    if b:
        return "Yes"
    else:
        return "No"


_EXPECTED_ITEMS = {
    RandovaniaGame.METROID_PRIME: {
        "Combat Visor",
        "Scan Visor",
        "Power Beam"
    },
    RandovaniaGame.METROID_PRIME_ECHOES: {
        "Combat Visor",
        "Scan Visor",
        "Morph Ball",
        "Power Beam",
        "Charge Beam",
    },
    RandovaniaGame.METROID_PRIME_CORRUPTION: {
        "Scan Visor",
        "Morph Ball",
        "Morph Ball Bombs",
        "Power Beam",
        "Charge Beam",
        "Space Jump Boots",
    },
    RandovaniaGame.SUPER_METROID: set(),
}
_CUSTOM_ITEMS = {
    "Cannon Ball",
    "Double Damage",
    "Unlimited Beam Ammo",
    "Unlimited Missiles",
}

PresetDescription = Tuple[str, List[str]]


def _require_majors_check(ammo_configuration: AmmoConfiguration, ammo_names: List[str]) -> List[bool]:
    result = [False] * len(ammo_names)

    name_index_mapping = {name: i for i, name in enumerate(ammo_names)}

    for ammo, state in ammo_configuration.items_state.items():
        if ammo.name in name_index_mapping:
            result[name_index_mapping[ammo.name]] = state.requires_major_item

    return result


def message_for_required_mains(ammo_configuration: AmmoConfiguration, message_to_item: Dict[str, str]):
    item_names = [item for item in message_to_item.values()]
    main_required = _require_majors_check(ammo_configuration, item_names)
    return dict(zip(message_to_item.keys(), main_required))


def has_shuffled_item(configuration: MajorItemsConfiguration, item_name: str) -> bool:
    for item, state in configuration.items_state.items():
        if item.name == item_name:
            return state.num_shuffled_pickups > 0
    return False


def _calculate_starting_items(game: RandovaniaGame, items_state: Dict[MajorItem, MajorItemState]) -> List[str]:
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
        return starting_items
    else:
        # If an expected item is missing, it's added as "No X". So empty starting_items means it's precisely vanilla
        return ["Vanilla"]


def _calculate_item_pool(game: RandovaniaGame, configuration: MajorItemsConfiguration) -> List[str]:
    item_pool = []

    unexpected_items = _EXPECTED_ITEMS[game] | _CUSTOM_ITEMS
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
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

    elif game == RandovaniaGame.METROID_PRIME_CORRUPTION:
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

    return item_pool


def _format_params_base(configuration: BaseConfiguration,
                        ) -> Dict[str, List[str]]:
    game_description = default_database.game_description_for(configuration.game)
    major_items = configuration.major_items_configuration

    template_strings = collections.defaultdict(list)

    # Item Placement
    randomization_mode = configuration.available_locations.randomization_mode

    if major_items.minimum_random_starting_items == major_items.maximum_random_starting_items:
        random_starting_items = "{}".format(major_items.minimum_random_starting_items)
    else:
        random_starting_items = "{} to {}".format(
            major_items.minimum_random_starting_items,
            major_items.maximum_random_starting_items,
        )

    template_strings["Item Placement"].append(configuration.trick_level.pretty_description)

    if randomization_mode != RandomizationMode.FULL:
        template_strings["Item Placement"].append(f"Randomization Mode: {randomization_mode.value}")

    template_strings["Item Placement"].append(f"Dangerous Actions: {configuration.logical_resource_action.long_name}")

    if random_starting_items != "0":
        template_strings["Item Placement"].append(f"Random Starting Items: {random_starting_items}")

    # Starting Items
    template_strings["Starting Items"] = _calculate_starting_items(configuration.game, major_items.items_state)

    # Item Pool
    item_pool = _calculate_item_pool(configuration.game, major_items)

    template_strings["Item Pool"].append(
        "Size: {} of {}".format(*pool_creator.calculate_pool_item_count(configuration))
    )
    if item_pool:
        template_strings["Item Pool"].append(", ".join(item_pool))

    # Difficulty
    template_strings["Difficulty"].append(
        f"Damage Strictness: {configuration.damage_strictness.long_name}"
    )
    if configuration.pickup_model_style != PickupModelStyle.ALL_VISIBLE:
        template_strings["Difficulty"].append(f"Pickup: {configuration.pickup_model_style.long_name} "
                                              f"({configuration.pickup_model_data_source.long_name})")

    # Gameplay
    starting_locations = configuration.starting_location.locations
    if len(starting_locations) == 1:
        area = game_description.world_list.area_by_area_location(next(iter(starting_locations)))
        starting_location = game_description.world_list.area_name(area)
    else:
        starting_location = "{} locations".format(len(starting_locations))

    template_strings["Gameplay"].append(f"Starting Location: {starting_location}")

    return template_strings


def fill_template_strings_from_tree(template_strings: Dict[str, List[str]], tree: Dict[str, List[Dict[str, bool]]]):
    for category, entries in tree.items():
        if category not in template_strings:
            template_strings[category] = []

        for entry in entries:
            messages = [message for message, flag in entry.items() if flag]
            if messages:
                template_strings[category].append(", ".join(messages))


def _echoes_format_params(configuration: EchoesConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration
    item_database = default_database.item_database_for_game(configuration.game)

    template_strings = _format_params_base(configuration)
    unified_ammo = configuration.ammo_configuration.items_state[item_database.ammo["Beam Ammo Expansion"]]

    # Difficulty
    if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (6, 1.2):
        template_strings["Difficulty"].append("Dark Aether: {:.2f} dmg/s Varia, {:.2f} dmg/s Dark".format(
            configuration.varia_suit_damage, configuration.dark_suit_damage
        ))

    if configuration.energy_per_tank != 100:
        template_strings["Difficulty"].append(f"Energy Tank: {configuration.energy_per_tank} energy")

    if configuration.safe_zone.heal_per_second != 1:
        template_strings["Difficulty"].append(f"Safe Zone: {configuration.safe_zone.heal_per_second:.2f} energy/s")

    extra_message_tree = {
        "Item Pool": [
            {
                "Progressive Suit": has_shuffled_item(major_items, "Progressive Suit"),
                "Progressive Grapple": has_shuffled_item(major_items, "Progressive Grapple"),
                "Split beam ammo": unified_ammo.pickup_count == 0,
            }
        ],
        "Difficulty": [
            {"1-HP Mode": configuration.dangerous_energy_tank},
        ],
        "Gameplay": [
            {f"Translator Gates: {configuration.translator_configuration.description()}": True},
            {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Power Bomb needs Main": "Power Bomb Expansion",
                }
            ),
            {"Warp to start": configuration.warp_to_start,
             "Menu Mod": configuration.menu_mod,
             "Final bosses removed": configuration.elevators.skip_final_bosses},
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    # Sky Temple Keys
    if configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
        template_strings["Item Pool"].append("Sky Temple Keys at all bosses")
    elif configuration.sky_temple_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        template_strings["Item Pool"].append("Sky Temple Keys at all guardians")
    else:
        template_strings["Item Pool"].append(f"{configuration.sky_temple_keys.num_keys} Sky Temple Keys")

    return template_strings


def _corruption_format_params(configuration: CorruptionConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration
    template_strings = _format_params_base(configuration)

    extra_message_tree = {
        "Item Pool": [
            {
                "Progressive Missile": has_shuffled_item(major_items, "Progressive Missile"),
                "Progressive Beam": has_shuffled_item(major_items, "Progressive Beam"),
            }
        ],
        "Difficulty": [
            {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
        ],
        "Gameplay": [
            {f"Teleporters: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Ship Missiles needs Main": "Ship Missile Expansion",
                }
            ),
            {"Final bosses removed": configuration.elevators.skip_final_bosses},
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    return template_strings


_PRIME1_CUTSCENE_MODE_DESCRIPTION = {
    LayoutCutsceneMode.MAJOR: "Major cutscene removal",
    LayoutCutsceneMode.MINOR: "Minor cutscene removal",
    LayoutCutsceneMode.COMPETITIVE: "Competitive cutscene removal",
    LayoutCutsceneMode.ORIGINAL: None,
}


def _prime_format_params(configuration: PrimeConfiguration) -> Dict[str, List[str]]:
    template_strings = _format_params_base(configuration)
    cutscene_removal = _PRIME1_CUTSCENE_MODE_DESCRIPTION[configuration.qol_cutscenes]

    extra_message_tree = {
        "Difficulty": [
            {"Heat Damage: {:.2f} dmg/s".format(configuration.heat_damage): configuration.heat_damage != 10.0},
            {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
        ],
        "Gameplay": [
            {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
            {"Underwater movement without Gravity allowed": configuration.allow_underwater_movement_without_gravity},
        ],
        "Quality of Life": [
            {
                "Fixes to game breaking bugs": configuration.qol_game_breaking,
                "Pickup scans": configuration.qol_pickup_scans,
            }
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Power Bomb needs Main": "Power Bomb Expansion",
                }
            ),
            {
                "Varia-only heat protection": configuration.heat_protection_only_varia,
                "Progressive suit damage reduction": configuration.progressive_damage_reduction,
            },
            {
                "Warp to start": configuration.warp_to_start,
                "Final bosses removed": configuration.elevators.skip_final_bosses,
                "Unlocked Vault door": configuration.main_plaza_door,
                "Phazon Elite without Dynamo": configuration.phazon_elite_without_dynamo,
            },
            {
                "Small Samus": configuration.small_samus,
            },
            {
                cutscene_removal: cutscene_removal is not None,
            }
        ],
    }

    fill_template_strings_from_tree(template_strings, extra_message_tree)

    backwards = [
        message
        for flag, message in [
            (configuration.backwards_frigate, "Frigate"),
            (configuration.backwards_labs, "Labs"),
            (configuration.backwards_upper_mines, "Upper Mines"),
            (configuration.backwards_lower_mines, "Lower Mines"),
        ]
        if flag
    ]
    if backwards:
        template_strings["Game Changes"].append("Allowed backwards: {}".format(", ".join(backwards)))

    # Artifacts
    template_strings["Item Pool"].append(f"{configuration.artifact_target.num_artifacts} Artifacts, "
                                         f"{configuration.artifact_minimum_progression} min actions")

    return template_strings


def describe(preset: Preset) -> Iterable[PresetDescription]:
    configuration = preset.configuration

    if preset.game == RandovaniaGame.METROID_PRIME_ECHOES:
        template_strings = _echoes_format_params(configuration)

    elif preset.game == RandovaniaGame.METROID_PRIME_CORRUPTION:
        template_strings = _corruption_format_params(configuration)

    elif preset.game == RandovaniaGame.METROID_PRIME:
        template_strings = _prime_format_params(configuration)

    else:
        template_strings = _format_params_base(configuration)

    if configuration.multi_pickup_placement:
        template_strings["Item Placement"].append("Multi-pickup placement")

    for category, entries in template_strings.items():
        if entries:
            yield category, entries


def merge_categories(categories: Iterable[PresetDescription]) -> str:
    return "".join(
        """<h4><span style="font-weight:600;">{}</span></h4><p>{}</p>""".format(category, "<br />".join(items))
        for category, items in categories
    )
