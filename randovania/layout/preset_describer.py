import collections
from typing import Iterable, Sequence

from randovania.game_description import default_database
from randovania.game_description.item.major_item import MajorItem
from randovania.generator.item_pool import pool_creator
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.preset import Preset


def _bool_to_str(b: bool) -> str:
    if b:
        return "Yes"
    else:
        return "No"


PresetDescription = tuple[str, list[str]]


class GamePresetDescriber:
    def _calculate_starting_items(self, configuration: BaseConfiguration) -> list[str]:
        expected_count = self.expected_starting_item_count(configuration)
        starting_items = []

        for major_item, item_state in configuration.major_items_configuration.items_state.items():
            if major_item.hide_from_gui:
                continue

            count = item_state.num_included_in_starting_items
            if count != expected_count[major_item]:
                if count > 1:
                    starting_items.append(f"{count}x {major_item.name}")
                elif count == 1:
                    starting_items.append(major_item.name)
                else:
                    starting_items.append(f"No {major_item.name}")

        if starting_items:
            return starting_items
        else:
            # If an expected item is missing, it's added as "No X". So empty starting_items means it's precisely vanilla
            return ["Vanilla"]

    def _calculate_item_pool(self, configuration: BaseConfiguration) -> list[str]:
        expected_count = self.expected_shuffled_item_count(configuration)
        item_pool = []

        for major_item, item_state in configuration.major_items_configuration.items_state.items():
            if major_item.hide_from_gui:
                continue

            count = item_state.num_shuffled_pickups + int(item_state.include_copy_in_original_location)
            if count != expected_count[major_item]:
                if count > 1:
                    item_pool.append(f"{count}x {major_item.name}")
                elif count == 1:
                    item_pool.append(major_item.name)
                else:
                    item_pool.append(f"No {major_item.name}")

        return item_pool

    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        """Function providing any game-specific information to display in presets such as the goal."""

        game_description = default_database.game_description_for(configuration.game)
        major_items = configuration.major_items_configuration

        template_strings = collections.defaultdict(list)

        # Item Placement
        randomization_mode = configuration.available_locations.randomization_mode

        if major_items.minimum_random_starting_items == major_items.maximum_random_starting_items:
            random_starting_items = f"{major_items.minimum_random_starting_items}"
        else:
            random_starting_items = "{} to {}".format(
                major_items.minimum_random_starting_items,
                major_items.maximum_random_starting_items,
            )

        template_strings["Logic Settings"].append(configuration.trick_level.pretty_description)
        template_strings["Logic Settings"].append(
            f"Dangerous Actions: {configuration.logical_resource_action.long_name}")

        if randomization_mode != RandomizationMode.FULL:
            template_strings["Item Placement"].append(f"Randomization Mode: {randomization_mode.value}")
        if configuration.multi_pickup_placement:
            template_strings["Item Placement"].append("Multi-pickup placement")
            if configuration.multi_pickup_new_weighting:
                template_strings["Item Placement"].append("New multi-pickup weighting")

        # Starting Items
        if random_starting_items != "0":
            template_strings["Starting Items"].append(f"Random Starting Items: {random_starting_items}")
        template_strings["Starting Items"].extend(self._calculate_starting_items(configuration))

        # Item Pool
        item_pool = self._calculate_item_pool(configuration)

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
            starting_location = f"{len(starting_locations)} locations"

        template_strings["Gameplay"].append(f"Starting Location: {starting_location}")

        # Dock Locks
        dock_mode = configuration.dock_rando.mode
        if dock_mode != DockRandoMode.VANILLA:
            template_strings["Door Locks"].append(f"Mode: {dock_mode.long_name} ({dock_mode.description})")

        return template_strings

    def expected_starting_item_count(self, configuration: BaseConfiguration) -> dict[MajorItem, int]:
        """Lists what are the expected starting item count.
        The configuration so it can vary based on progressive settings, as example."""
        return {
            major: major.default_starting_count
            for major in configuration.major_items_configuration.items_state.keys()
        }

    def expected_shuffled_item_count(self, configuration: BaseConfiguration) -> dict[MajorItem, int]:
        """Lists what are the expected shuffled item count.
        The configuration so it can vary based on progressive settings, as example."""
        return {
            major: major.default_shuffled_count
            for major in configuration.major_items_configuration.items_state.keys()
        }


def _require_majors_check(ammo_configuration: AmmoConfiguration, ammo_names: list[str]) -> list[bool]:
    result = [False] * len(ammo_names)

    name_index_mapping = {name: i for i, name in enumerate(ammo_names)}

    for ammo, state in ammo_configuration.items_state.items():
        if ammo.name in name_index_mapping:
            result[name_index_mapping[ammo.name]] = state.requires_major_item

    return result


def message_for_required_mains(ammo_configuration: AmmoConfiguration, message_to_item: dict[str, str]):
    item_names = [item for item in message_to_item.values()]
    main_required = _require_majors_check(ammo_configuration, item_names)
    return dict(zip(message_to_item.keys(), main_required))


def has_shuffled_item(configuration: MajorItemsConfiguration, item_name: str) -> bool:
    for item, state in configuration.items_state.items():
        if item.name == item_name:
            return (state.num_shuffled_pickups + int(state.include_copy_in_original_location)) > 0
    return False


def has_vanilla_item(configuration: MajorItemsConfiguration, item_name: str) -> bool:
    for item, state in configuration.items_state.items():
        if item.name == item_name:
            return state.include_copy_in_original_location
    return False


def fill_template_strings_from_tree(template_strings: dict[str, list[str]], tree: dict[str, list[dict[str, bool]]]):
    for category, entries in tree.items():
        if category not in template_strings:
            template_strings[category] = []

        for entry in entries:
            messages = [message for message, flag in entry.items() if flag]
            if messages:
                template_strings[category].append(", ".join(messages))


def describe(preset: Preset) -> Iterable[PresetDescription]:
    configuration = preset.configuration

    template_strings = preset.game.data.layout.preset_describer.format_params(configuration)

    for category, entries in template_strings.items():
        if entries:
            yield category, entries


def merge_categories(categories: Iterable[PresetDescription]) -> str:
    return "".join(
        """<h4><span style="font-weight:600;">{}</span></h4><p>{}</p>""".format(category, "<br />".join(items))
        for category, items in categories
    )


def handle_progressive_expected_counts(counts: dict[MajorItem, int], configuration: MajorItemsConfiguration,
                                       progressive: str, non_progressive: Sequence[str]) -> None:
    progressive_item = configuration.get_item_with_name(progressive)
    non_progressive_items = [configuration.get_item_with_name(name) for name in non_progressive]

    if has_shuffled_item(configuration, progressive):
        counts[progressive_item] = len(non_progressive)
        for p in non_progressive_items:
            counts[p] = 0
    else:
        counts[progressive_item] = 0
        for p in non_progressive_items:
            counts[p] = 1
