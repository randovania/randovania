import collections
from typing import Iterable, Sequence

from randovania.game_description import default_database
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
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

        for standard_pickup, pickup_state in configuration.standard_pickup_configuration.pickups_state.items():
            if standard_pickup.hide_from_gui:
                continue

            count = pickup_state.num_included_in_starting_pickups
            if count != expected_count[standard_pickup]:
                if count > 1:
                    starting_items.append(f"{count}x {standard_pickup.name}")
                elif count == 1:
                    starting_items.append(standard_pickup.name)
                else:
                    starting_items.append(f"No {standard_pickup.name}")

        if starting_items:
            return starting_items
        else:
            # If an expected item is missing, it's added as "No X". So empty starting_items means it's precisely vanilla
            return ["Vanilla"]

    def _calculate_item_pool(self, configuration: BaseConfiguration) -> list[str]:
        expected_count = self.expected_shuffled_pickup_count(configuration)
        item_pool = []

        for standard_pickup, pickup_state in configuration.standard_pickup_configuration.pickups_state.items():
            if standard_pickup.hide_from_gui:
                continue

            count = pickup_state.num_shuffled_pickups + int(pickup_state.include_copy_in_original_location)
            if count != expected_count[standard_pickup]:
                if count > 1:
                    item_pool.append(f"{count}x {standard_pickup.name}")
                elif count == 1:
                    item_pool.append(standard_pickup.name)
                else:
                    item_pool.append(f"No {standard_pickup.name}")

        return item_pool

    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        """Function providing any game-specific information to display in presets such as the goal."""

        game_description = default_database.game_description_for(configuration.game)
        standard_pickups = configuration.standard_pickup_configuration

        template_strings = collections.defaultdict(list)

        unsupported = configuration.unsupported_features()
        if unsupported:
            template_strings["WARNING!"] = [
                "This preset uses the following unsupported features:",
                ", ".join(unsupported)
            ]

        # Item Placement
        randomization_mode = configuration.available_locations.randomization_mode

        if standard_pickups.minimum_random_starting_pickups == standard_pickups.maximum_random_starting_pickups:
            random_starting_pickups = f"{standard_pickups.minimum_random_starting_pickups}"
        else:
            random_starting_pickups = "{} to {}".format(
                standard_pickups.minimum_random_starting_pickups,
                standard_pickups.maximum_random_starting_pickups,
            )

        template_strings["Logic Settings"].append(configuration.trick_level.pretty_description(game_description))
        template_strings["Logic Settings"].append(
            f"Dangerous Actions: {configuration.logical_resource_action.long_name}")

        if configuration.single_set_for_pickups_that_solve:
            template_strings["Logic Settings"].append("Experimental potential actions")

        if configuration.staggered_multi_pickup_placement:
            template_strings["Logic Settings"].append("Experimental staggered pickups")

        if randomization_mode != RandomizationMode.FULL:
            template_strings["Item Placement"].append(f"Randomization Mode: {randomization_mode.value}")

        # Starting Items
        if random_starting_pickups != "0":
            template_strings["Starting Items"].append(f"Random Starting Items: {random_starting_pickups}")
        template_strings["Starting Items"].extend(self._calculate_starting_items(configuration))

        # Item Pool
        item_pool = self._calculate_item_pool(configuration)

        template_strings["Item Pool"].append(
            "Size: {} of {}".format(*pool_creator.calculate_pool_pickup_count(configuration))
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

    def expected_starting_item_count(self, configuration: BaseConfiguration) -> dict[StandardPickupDefinition, int]:
        """Lists what are the expected starting item count.
        The configuration so it can vary based on progressive settings, as example."""
        return {
            major: major.default_starting_count
            for major in configuration.standard_pickup_configuration.pickups_state.keys()
        }

    def expected_shuffled_pickup_count(self, configuration: BaseConfiguration) -> dict[StandardPickupDefinition, int]:
        """Lists what are the expected shuffled item count.
        The configuration so it can vary based on progressive settings, as example."""
        return {
            major: major.default_shuffled_count
            for major in configuration.standard_pickup_configuration.pickups_state.keys()
        }


def _require_majors_check(ammo_configuration: AmmoPickupConfiguration, ammo_names: list[str]) -> list[bool]:
    result = [False] * len(ammo_names)

    name_index_mapping = {name: i for i, name in enumerate(ammo_names)}

    for ammo, state in ammo_configuration.pickups_state.items():
        if ammo.name in name_index_mapping:
            result[name_index_mapping[ammo.name]] = state.requires_main_item

    return result


def message_for_required_mains(ammo_configuration: AmmoPickupConfiguration, message_to_item: dict[str, str]):
    item_names = [item for item in message_to_item.values()]
    main_required = _require_majors_check(ammo_configuration, item_names)
    return dict(zip(message_to_item.keys(), main_required))


def has_shuffled_item(configuration: StandardPickupConfiguration, item_name: str) -> bool:
    for item, state in configuration.pickups_state.items():
        if item.name == item_name:
            return (state.num_shuffled_pickups + int(state.include_copy_in_original_location)) > 0
    return False


def has_vanilla_item(configuration: StandardPickupConfiguration, item_name: str) -> bool:
    for item, state in configuration.pickups_state.items():
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


def handle_progressive_expected_counts(counts: dict[StandardPickupDefinition, int],
                                       configuration: StandardPickupConfiguration,
                                       progressive: str, non_progressive: Sequence[str]) -> None:
    progressive_item = configuration.get_pickup_with_name(progressive)
    non_progressive_items = [configuration.get_pickup_with_name(name) for name in non_progressive]

    if has_shuffled_item(configuration, progressive):
        counts[progressive_item] = len(non_progressive)
        for p in non_progressive_items:
            counts[p] = 0
    else:
        counts[progressive_item] = 0
        for p in non_progressive_items:
            counts[p] = 1
