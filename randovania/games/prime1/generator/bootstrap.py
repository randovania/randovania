from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.prime1.layout.prime_configuration import DamageReduction as DamageReductionConfig
from randovania.games.prime1.layout.prime_configuration import IngameDifficulty, PrimeConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from collections.abc import Callable
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState


def is_pickup_to_pre_place(pickup: PickupEntry, configuration: PrimeConfiguration) -> bool:
    if configuration.pre_place_artifact and pickup.gui_category.name == "artifact":
        return True
    if configuration.pre_place_phazon and pickup.name == "Phazon Suit":
        return True
    return False


def is_location_to_pre_place(node: PickupNode, configuration: PrimeConfiguration) -> bool:
    return True


def is_major_artifact_location_predicate(game: GameDescription) -> Callable[[PickupNode, PrimeConfiguration], bool]:
    def is_major_artifact_location(node: PickupNode, config: PrimeConfiguration) -> bool:
        return game.region_list.node_from_pickup_index(node.pickup_index).location_category == LocationCategory.MAJOR

    return is_major_artifact_location


def get_artifact_location_predicate(
    game: GameDescription, config: PrimeConfiguration
) -> Callable[[PickupNode, PrimeConfiguration], bool]:
    return (
        is_location_to_pre_place
        if config.available_locations.randomization_mode == RandomizationMode.FULL
        else is_major_artifact_location_predicate(game)
    )


class PrimeBootstrap(Bootstrap):
    def create_damage_state(self, game: GameDatabaseView, configuration: BaseConfiguration) -> DamageState:
        assert isinstance(configuration, PrimeConfiguration)
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("EnergyTank"),
        )

    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        assert isinstance(configuration, PrimeConfiguration)
        enabled_resources = set()

        logical_patches = {
            "allow_underwater_movement_without_gravity": "NoGravity",
            "main_plaza_door": "main_plaza_door",
            "backwards_frigate": "backwards_frigate",
            "backwards_labs": "backwards_labs",
            "backwards_upper_mines": "backwards_upper_mines",
            "backwards_lower_mines": "backwards_lower_mines",
            "phazon_elite_without_dynamo": "phazon_elite_without_dynamo",
            "small_samus": "small",
            "large_samus": "large_samus",
            "shuffle_item_pos": "shuffle_item_pos",
            "items_every_room": "items_every_room",
            "random_boss_sizes": "random_boss_sizes",
            "no_doors": "no_doors",
            "superheated_probability": "superheated_probability",
            "submerged_probability": "submerged_probability",
            "remove_bars_great_tree_hall": "remove_bars_great_tree_hall",
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("dock_rando")

        if configuration.ingame_difficulty == IngameDifficulty.HARD:
            enabled_resources.add("hard_mode")

        if configuration.legacy_mode:
            enabled_resources.add("vanilla_heat")

        return enabled_resources

    def prime1_progressive_damage_reduction(
        self, db: ResourceDatabaseView, current_resources: ResourceCollection
    ) -> float:
        num_suits = sum(
            current_resources[db.get_item_by_display_name(suit)]
            for suit in ["Varia Suit", "Gravity Suit", "Phazon Suit"]
        )
        if num_suits >= 3:
            dr = 0.5
        elif num_suits == 2:
            dr = 0.8
        elif num_suits == 1:
            dr = 0.9
        else:
            dr = 1

        hard_mode = db.get_misc("hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def prime1_additive_damage_reduction(
        self, db: ResourceDatabaseView, current_resources: ResourceCollection
    ) -> float:
        dr = 1.0
        if current_resources[db.get_item_by_display_name("Varia Suit")]:
            dr -= 0.1
        if current_resources[db.get_item_by_display_name("Gravity Suit")]:
            dr -= 0.1
        if current_resources[db.get_item_by_display_name("Phazon Suit")]:
            dr -= 0.3

        hard_mode = db.get_misc("hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def prime1_absolute_damage_reduction(
        self, db: ResourceDatabaseView, current_resources: ResourceCollection
    ) -> float:
        if current_resources[db.get_item_by_display_name("Phazon Suit")] > 0:
            dr = 0.5
        elif current_resources[db.get_item_by_display_name("Gravity Suit")] > 0:
            dr = 0.8
        elif current_resources[db.get_item_by_display_name("Varia Suit")] > 0:
            dr = 0.9
        else:
            dr = 1

        hard_mode = db.get_misc("hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        assert isinstance(configuration, PrimeConfiguration)

        damage_reductions = copy.copy(db.damage_reductions)
        requirement_template = copy.copy(db.requirement_template)

        suits = [db.get_item_by_display_name("Varia Suit")]
        if configuration.legacy_mode:
            suits.extend([db.get_item_by_display_name("Gravity Suit"), db.get_item_by_display_name("Phazon Suit")])

        reductions = [DamageReduction(None, configuration.heat_damage / 10.0)]
        reductions.extend([DamageReduction(suit, 0) for suit in suits])
        damage_reductions[db.get_damage("HeatDamage1")] = reductions

        if configuration.damage_reduction == DamageReductionConfig.PROGRESSIVE:
            base_damage_reduction = self.prime1_progressive_damage_reduction
        elif configuration.damage_reduction == DamageReductionConfig.ADDITIVE:
            base_damage_reduction = self.prime1_additive_damage_reduction
        else:
            base_damage_reduction = self.prime1_absolute_damage_reduction

        return dataclasses.replace(
            db,
            damage_reductions=damage_reductions,
            base_damage_reduction=base_damage_reduction,
            requirement_template=requirement_template,
        )

    def assign_pool_results(
        self, rng: Random, configuration: PrimeConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        pickups_to_preplace = [
            pickup for pickup in list(pool_results.to_place) if is_pickup_to_pre_place(pickup, configuration)
        ]
        locations = self.all_preplaced_pickup_locations(
            patches.game, configuration, get_artifact_location_predicate(patches.game, configuration)
        )
        weighted_locations = {location: location.extra.get("regional_weight", 1.0) for location in locations}
        self.pre_place_pickups_weighted(rng, pickups_to_preplace, weighted_locations, pool_results, patches.game.game)
        return super().assign_pool_results(rng, configuration, patches, pool_results)
