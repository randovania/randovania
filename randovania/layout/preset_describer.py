import collections
from collections.abc import Iterable, Sequence

from randovania.game_description import default_database
from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
from randovania.game_description.resources.location_category import LocationCategory
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.damage_strictness import LayoutDamageStrictness
from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
from randovania.layout.base.pickup_model import PickupModelStyle
from randovania.layout.preset import Preset


PresetDescription = tuple[str, list[str]]


class GamePresetDescriber:
    def _calculate_pickup_pool(self, configuration: BaseConfiguration) -> list[str]:
        expected_starting_count = self.expected_starting_item_count(configuration)
        expected_shuffled_count = self.expected_shuffled_pickup_count(configuration)
        shuffled_list = []
        starting_list = []
        is_vanilla_starting = True
        excluded_list = []

        for standard_pickup, pickup_state in configuration.standard_pickup_configuration.pickups_state.items():
            if standard_pickup.hide_from_gui:
                continue

            starting_count = pickup_state.num_included_in_starting_pickups
            shuffled_count = pickup_state.num_shuffled_pickups + int(pickup_state.include_copy_in_original_location)

            if starting_count != expected_starting_count[standard_pickup]:
                if starting_count > 1:
                    starting_list.append(f"{starting_count}x {standard_pickup.name}")
                elif starting_count == 1:
                    starting_list.append(standard_pickup.name)
                else:
                    is_vanilla_starting = False
                    if shuffled_count == 0:
                        excluded_list.append(standard_pickup.name)

            if shuffled_count != expected_shuffled_count[standard_pickup]:
                if shuffled_count > 1:
                    shuffled_list.append(f"{shuffled_count}x {standard_pickup.name}")
                elif shuffled_count == 1:
                    shuffled_list.append(standard_pickup.name)
                elif starting_count == 0:
                    excluded_list.append(standard_pickup.name)

        result = []

        if starting_list:
            result.append("Starts with " + ", ".join(starting_list))
        elif is_vanilla_starting:
            result.append("Vanilla starting items")

        if excluded_list:
            result.append("Excludes " + ", ".join(excluded_list))

        if shuffled_list:
            result.append("Shuffles " + ", ".join(shuffled_list))

        return result

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

        if not configuration.logical_resource_action.is_default():
            template_strings["Logic Settings"].append(
                f"{configuration.logical_resource_action.long_name} dangerous actions"
            )

        if configuration.single_set_for_pickups_that_solve:
            template_strings["Logic Settings"].append("Experimental potential actions")

        if configuration.staggered_multi_pickup_placement:
            template_strings["Logic Settings"].append("Experimental staggered pickups")

        if randomization_mode != RandomizationMode.default():
            template_strings["Item Pool"].append(randomization_mode.description)

        # Item Pool
        per_category_pool = pool_creator.calculate_pool_pickup_count(configuration)
        if configuration.available_locations.randomization_mode is RandomizationMode.FULL:
            pool_items, maximum_size = pool_creator.get_total_pickup_count(per_category_pool)
            template_strings["Item Pool"].append(f"Size: {pool_items} of {maximum_size}")
        else:
            for category, (count, num_nodes) in per_category_pool.items():
                if isinstance(category, LocationCategory):
                    template_strings["Item Pool"].append(f"{category.long_name}: {count}/{num_nodes}")

        if random_starting_pickups != "0":
            template_strings["Item Pool"].append(f"{random_starting_pickups} random starting items")

        template_strings["Item Pool"].extend(self._calculate_pickup_pool(configuration))

        # Difficulty
        if configuration.damage_strictness != LayoutDamageStrictness.MEDIUM:
            template_strings["Difficulty"].append(
                f"{configuration.damage_strictness.long_name} damage strictness"
        )
        if configuration.pickup_model_style != PickupModelStyle.ALL_VISIBLE:
            template_strings["Difficulty"].append(f"Pickup: {configuration.pickup_model_style.long_name} "
                                                  f"({configuration.pickup_model_data_source.long_name})")

        # Gameplay
        starting_locations = configuration.starting_location.locations
        if len(starting_locations) == 1:
            area = game_description.region_list.area_by_area_location(starting_locations[0])
            starting_location = f"Starts at {game_description.region_list.area_name(area)}"
        else:
            starting_location = f"{len(starting_locations)} starting locations"
        template_strings["Gameplay"].append(starting_location)

        # Dock Locks
        dock_rando = configuration.dock_rando
        if dock_rando.is_enabled():
            template_strings["Gameplay"].append(dock_rando.mode.description)

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
