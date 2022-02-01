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


def _bool_to_str(b: bool) -> str:
    if b:
        return "Yes"
    else:
        return "No"


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


def has_vanilla_item(configuration: MajorItemsConfiguration, item_name: str) -> bool:
    for item, state in configuration.items_state.items():
        if item.name == item_name:
            return state.include_copy_in_original_location
    return False


def _calculate_starting_items(game: RandovaniaGame, items_state: Dict[MajorItem, MajorItemState]) -> List[str]:
    expected_items = game.data.layout.preset_describer.expected_items
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

    unexpected_items = game.data.layout.preset_describer.unexpected_items(configuration)

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
                        ) -> dict[str, list[str]]:
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

    template_strings["Logic Settings"].append(configuration.trick_level.pretty_description)
    template_strings["Logic Settings"].append(f"Dangerous Actions: {configuration.logical_resource_action.long_name}")

    if randomization_mode != RandomizationMode.FULL:
        template_strings["Item Placement"].append(f"Randomization Mode: {randomization_mode.value}")
    if configuration.multi_pickup_placement:
        template_strings["Item Placement"].append("Multi-pickup placement")

    # Starting Items
    if random_starting_items != "0":
        template_strings["Starting Items"].append(f"Random Starting Items: {random_starting_items}")
    template_strings["Starting Items"].extend(_calculate_starting_items(configuration.game, major_items.items_state))

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
        area = game_description.world_list.area_by_area_location(starting_locations[0])
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


def describe(preset: Preset) -> Iterable[PresetDescription]:
    configuration = preset.configuration

    template_strings = (preset.game.data.layout.preset_describer.format_params or _format_params_base)(configuration)

    for category, entries in template_strings.items():
        if entries:
            yield category, entries


def merge_categories(categories: Iterable[PresetDescription]) -> str:
    return "".join(
        """<h4><span style="font-weight:600;">{}</span></h4><p>{}</p>""".format(category, "<br />".join(items))
        for category, items in categories
    )
