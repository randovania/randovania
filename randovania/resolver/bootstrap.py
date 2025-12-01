from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_type import ResourceType
from randovania.generator.pickup_pool.pickup_creator import create_ammo_pickup, create_standard_pickup
from randovania.generator.pickup_pool.standard_pickup import find_ammo_for
from randovania.graph import world_graph_factory
from randovania.graph.state import State
from randovania.layout.base.logical_pickup_placement_configuration import LogicalPickupPlacementConfiguration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.exceptions import InvalidConfiguration
from randovania.lib import random_lib

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable
    from random import Random

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.game_description import GameDescription, MinimalLogicData
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceQuantity
    from randovania.generator.pickup_pool import PoolResults
    from randovania.graph import world_graph
    from randovania.graph.world_graph import WorldGraph
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration
    from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
    from randovania.resolver.damage_state import DamageState


def enabled_standard_pickups(game: GameDescription, configuration: BaseConfiguration) -> Generator[PickupEntry]:
    for pickup, state in configuration.standard_pickup_configuration.pickups_state.items():
        if len(pickup.ammo) != len(state.included_ammo):
            raise InvalidConfiguration(
                f"Item {pickup.name} uses {pickup.ammo} as ammo, "
                f"but there's only {len(state.included_ammo)} values in included_ammo"
            )

        ammo, locked_ammo = find_ammo_for(pickup.ammo, configuration.ammo_pickup_configuration)

        if state.include_copy_in_original_location:
            if not pickup.original_locations:
                raise InvalidConfiguration(
                    f"Item {pickup.name} does not exist in the original game, cannot use state {state}",
                )
            for _ in pickup.original_locations:
                yield create_standard_pickup(pickup, state, game.get_resource_database_view(), ammo, locked_ammo)

        for _ in range(state.num_shuffled_pickups):
            yield create_standard_pickup(pickup, state, game.get_resource_database_view(), ammo, locked_ammo)

        for _ in range(state.num_included_in_starting_pickups):
            yield create_standard_pickup(pickup, state, game.get_resource_database_view(), ammo, locked_ammo)


def enabled_ammo_pickups(game: GameDescription, configuration: BaseConfiguration) -> Generator[PickupEntry]:
    for ammo, state in configuration.ammo_pickup_configuration.pickups_state.items():
        pickup = create_ammo_pickup(ammo, state.ammo_count, state.requires_main_item, game.get_resource_database_view())
        for _ in range(state.pickup_count):
            yield pickup


def enabled_pickups(game: GameDescription, configuration: BaseConfiguration) -> Generator[PickupEntry]:
    yield from enabled_standard_pickups(game, configuration)
    yield from enabled_ammo_pickups(game, configuration)


def victory_condition_for_pickup_placement(
    pickups: Iterable[PickupEntry], game: GameDescription, placement_config: LogicalPickupPlacementConfiguration
) -> Requirement:
    """
    Creates a Requirement with the game's victory condition adjusted to a specified pickup set.
    :param pickups:
    :param game:
    :param placement_config: The configuration for adjusting the victory condition.
    :return:
    """
    if placement_config is LogicalPickupPlacementConfiguration.MINIMAL:
        return game.victory_condition

    add_all_pickups = placement_config is LogicalPickupPlacementConfiguration.ALL
    resources = game.resource_database.create_resource_collection()

    for pickup in pickups:
        if pickup.generator_params.preferred_location_category is LocationCategory.MAJOR or add_all_pickups:
            resources.add_resource_gain(pickup.resource_gain(resources, force_lock=True))

    # Create a requirement with the victory condition and the pickups
    return RequirementAnd(
        [
            game.victory_condition,
            *(
                ResourceRequirement.create(resource, quantity, False)
                for resource, quantity in resources.as_resource_gain()
                if quantity > 0
                and isinstance(resource, ItemResourceInfo)
                and not resource.extra.get("exclude_from_logical_pickup_placement", False)
            ),
        ]
    ).simplify()


class EnergyConfig(NamedTuple):
    starting_energy: int
    energy_per_tank: int


class Bootstrap[Configuration: BaseConfiguration]:
    def trick_resources_for_configuration(
        self,
        configuration: TrickLevelConfiguration,
        resource_database: ResourceDatabaseView,
    ) -> ResourceGain:
        """
        :param configuration:
        :param resource_database:
        :return:
        """
        for trick in resource_database.get_all_tricks():
            if configuration.minimal_logic:
                level = LayoutTrickLevel.maximum()
            else:
                level = configuration.level_for_trick(trick)

            yield trick, level.as_number

    def event_resources_for_configuration(
        self,
        configuration: Configuration,
        resource_database: ResourceDatabaseView,
    ) -> ResourceGain:
        yield from []

    def minimal_logic_initial_resources(
        self,
        minimal_logic: MinimalLogicData,
        resource_database: ResourceDatabaseView,
        standard_pickups: StandardPickupConfiguration,
    ) -> ResourceGain:
        resource_gain: list[ResourceQuantity] = []

        items_to_skip = set()

        item_db = default_database.pickup_database_for_game(standard_pickups.game)
        pickups_state = standard_pickups.pickups_state
        custom_item_count = minimal_logic.custom_item_amount

        for it in minimal_logic.items_to_exclude:
            if it.reason is None or pickups_state[item_db.standard_pickups[it.reason]].num_shuffled_pickups != 0:
                items_to_skip.add(it.name)

        resource_gain.extend(
            (item, custom_item_count.get(item.short_name, 1))
            for item in resource_database.get_all_items()
            if item.short_name not in items_to_skip
        )

        events_to_skip = {it.name for it in minimal_logic.events_to_exclude}
        resource_gain.extend(
            (event, 1) for event in resource_database.get_all_events() if event.short_name not in events_to_skip
        )

        return resource_gain

    def create_damage_state(self, game: GameDatabaseView, configuration: Configuration) -> DamageState:
        """
        Creates a DamageState for the given configuration.
        :param game:
        :param configuration:
        :return:
        """
        raise NotImplementedError

    def version_resources_for_game(
        self, configuration: Configuration, resource_database: ResourceDatabaseView
    ) -> ResourceGain:
        """
        Determines which Version resources should be enabled, according to the configuration.
        Override as needed.
        """
        # Only enable one specific version
        for resource in resource_database.get_all_resources_of_type(ResourceType.VERSION):
            yield resource, 1 if resource.long_name == "NTSC" else 0

    def _get_enabled_misc_resources(
        self, configuration: Configuration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        """
        Returns a set of strings corresponding to Misc resource short names which should be enabled.
        Override as needed.
        """
        return set()

    def misc_resources_for_configuration(
        self, configuration: Configuration, resource_database: ResourceDatabaseView
    ) -> ResourceGain:
        """
        Determines which Misc resources should be enabled, according to the configuration.
        """
        enabled_resources = self._get_enabled_misc_resources(configuration, resource_database)
        for resource in resource_database.get_all_resources_of_type(ResourceType.MISC):
            yield resource, 1 if resource.short_name in enabled_resources else 0

    def starting_resources_for_patches(
        self,
        configuration: Configuration,
        resource_view: ResourceDatabaseView,
        patches: GamePatches,
    ) -> ResourceCollection:
        collection = patches.starting_resources()

        # When calling `patch_requirement`, not-set is different to `set to 0`.
        keys_to_remove = [resource for resource, quantity in collection.as_resource_gain() if quantity == 0]
        for resource in keys_to_remove:
            collection.remove_resource(resource)

        if configuration.trick_level.minimal_logic:
            minimal_logic = configuration.game.game_description.minimal_logic
            if minimal_logic is None:
                raise ValueError(f"Minimal logic enabled, but {configuration.game} doesn't have support for it.")

            collection.add_resource_gain(
                self.minimal_logic_initial_resources(
                    minimal_logic, resource_view, configuration.standard_pickup_configuration
                )
            )

        collection.add_resource_gain(self.trick_resources_for_configuration(configuration.trick_level, resource_view))
        collection.add_resource_gain(self.event_resources_for_configuration(configuration, resource_view))
        collection.add_resource_gain(self.version_resources_for_game(configuration, resource_view))
        collection.add_resource_gain(self.misc_resources_for_configuration(configuration, resource_view))

        return collection

    def patch_resource_database(self, db: ResourceDatabase, configuration: Configuration) -> ResourceDatabase:
        """
        Makes modifications to the resource database according to the configuration.
        Requirement templates and damage reductions are common candidates for modification.
        Override as needed.
        """
        return db

    def calculate_starting_state(
        self,
        resources: ResourceCollection,
        graph: WorldGraph,
        game: GameDescription,
        configuration: Configuration,
        patches: GamePatches,
    ) -> State:
        return State(
            resources.duplicate(),
            {},
            (),
            self.create_damage_state(game, configuration).apply_collected_resource_difference(
                resources, game.get_resource_database_view().create_resource_collection()
            ),
            graph.node_identifier_to_node[patches.starting_location],
            patches,
            None,
            game.resource_database,
            game.region_list,
            hint_state=None,
        )

    def logic_bootstrap_graph(
        self, configuration: Configuration, game: GameDescription, patches: GamePatches
    ) -> tuple[world_graph.WorldGraph, State]:
        """
        Core code for starting a new Logic/State.
        :param configuration:
        :param game:
        :param patches:
        :return:
        """
        if not game.mutable:
            raise ValueError("Running logic_bootstrap with non-mutable game")

        self.apply_game_specific_patches(configuration, game, patches)

        # All majors/pickups required
        game.victory_condition = victory_condition_for_pickup_placement(
            enabled_pickups(game, configuration), game, configuration.logical_pickup_placement
        )

        static_resources = self.starting_resources_for_patches(
            configuration, game.get_resource_database_view(), patches
        )
        graph = world_graph_factory.create_graph(
            database_view=game,
            patches=patches,
            static_resources=static_resources,
            damage_multiplier=configuration.damage_strictness.value,
            victory_condition=game.victory_condition,
            flatten_to_set_on_patch=game.region_list.flatten_to_set_on_patch,
        )

        starting_state = self.calculate_starting_state(
            static_resources,
            graph,
            game,
            configuration,
            patches,
        )
        # This existed to collect the starting ship for Corruption, but it might cause issues with starting on docks
        # starting_state.resources.add_resource_gain(
        #     starting_state.node.resource_gain_on_collect(starting_state.node_context())
        # )

        return graph, starting_state

    def apply_game_specific_patches(
        self, configuration: Configuration, game: GameDescription, patches: GamePatches
    ) -> None:
        pass

    def assign_pool_results(
        self, rng: Random, configuration: Configuration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        return patches.assign_own_pickups(pool_results.assignment.items()).assign_extra_starting_pickups(
            pool_results.starting
        )

    def all_preplaced_pickup_locations(
        self,
        game: GameDatabaseView,
        config: Configuration,
        game_specific_check: Callable[[PickupNode, Configuration], bool],
    ) -> list[PickupNode]:
        locations = []

        for _, _, node in game.iterate_nodes_of_type(PickupNode):
            if (
                game_specific_check(node, config)
                and node.pickup_index not in config.available_locations.excluded_indices
            ):
                locations.append(node)

        return locations

    def pre_place_pickups_weighted(
        self,
        rng: Random,
        pickups_to_place: list[PickupEntry],
        locations: dict[PickupNode, float],
        pool_results: PoolResults,
        game: RandovaniaGame,
    ) -> None:
        """
        Pre-places a list of PickupEntry(s) from a set of weighted PickupNodes.
        """
        pre_placed_indices = list(pool_results.assignment.keys())
        reduced_locations = {loc: v for loc, v in locations.items() if loc.pickup_index not in pre_placed_indices}

        # weighted_locations is a list filled by selecting weighted elements from reduced_locations
        weighted_locations = []
        while reduced_locations:
            loc = random_lib.select_element_with_weight_and_uniform_fallback(rng, reduced_locations)
            weighted_locations.append(loc)
            reduced_locations.pop(loc)

        if len(pickups_to_place) > len(weighted_locations):
            raise InvalidConfiguration(
                f"Has {len(pickups_to_place)} pre-placed pickups in the pool, "
                f"but only {len(weighted_locations)} valid locations."
            )

        # places a pickup in the next location of weighted_locations until pickups_to_place is exhausted
        for pickup, location in zip(pickups_to_place, weighted_locations, strict=False):
            pool_results.to_place.remove(pickup)
            pool_results.assignment[location.pickup_index] = pickup

    def pre_place_pickups(
        self,
        rng: Random,
        pickups_to_place: list[PickupEntry],
        locations: list[PickupNode],
        pool_results: PoolResults,
        game: RandovaniaGame,
    ) -> None:
        """
        Calls pre_place_pickups_weighted with all weightings set to 1.0.
        """
        self.pre_place_pickups_weighted(
            rng,
            pickups_to_place,
            dict.fromkeys(locations, 1.0),
            pool_results,
            game,
        )
