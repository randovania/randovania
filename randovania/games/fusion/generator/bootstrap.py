from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.fusion.layout import FusionConfiguration
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
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_metroid_location(node: PickupNode, config: FusionConfiguration) -> bool:
    # Returns True for all locations, enabling Metroids to be pre-placed at any PickupNode
    return True


def is_major_metroid_location_predicate(game: GameDescription) -> Callable[[PickupNode, FusionConfiguration], bool]:
    def is_major_metroid_location(node: PickupNode, config: FusionConfiguration) -> bool:
        return game.region_list.node_from_pickup_index(node.pickup_index).location_category == LocationCategory.MAJOR

    return is_major_metroid_location


def get_metroid_location_predicate(
    game: GameDescription, config: FusionConfiguration
) -> Callable[[PickupNode, FusionConfiguration], bool]:
    return (
        is_metroid_location
        if config.available_locations.randomization_mode == RandomizationMode.FULL
        else is_major_metroid_location_predicate(game)
    )


class FusionBootstrap(Bootstrap[FusionConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: FusionConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("EnergyTank"),
        )

    def _get_enabled_misc_resources(
        self, configuration: FusionConfiguration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        enabled_resources = set()
        if configuration.dock_rando.is_enabled():
            enabled_resources.add("DoorLockRando")
        enabled_resources.add("BomblessPBs")
        enabled_resources.add("GeneratorHack")
        return enabled_resources

    def _damage_reduction(self, db: ResourceDatabaseView, current_resources: ResourceCollection) -> float:
        num_suits = sum(
            (1 if current_resources[db.get_item_by_display_name(suit)] else 0)
            for suit in ("Varia Suit", "Gravity Suit")
        )
        dr = 1.0
        if num_suits == 1:
            dr = 0.9
        elif num_suits >= 2:
            dr = 0.8

        return dr

    def patch_resource_database(self, db: ResourceDatabase, configuration: FusionConfiguration) -> ResourceDatabase:
        return dataclasses.replace(db, base_damage_reduction=self._damage_reduction)

    def assign_pool_results(
        self, rng: Random, configuration: FusionConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        pickups_to_preplace = [
            pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "InfantMetroid"
        ]
        locations = self.all_preplaced_pickup_locations(
            patches.game, configuration, get_metroid_location_predicate(patches.game, configuration)
        )
        weighted_locations = {location: location.extra["infant_weight"] for location in locations}
        self.pre_place_pickups_weighted(rng, pickups_to_preplace, weighted_locations, pool_results, patches.game.game)
        return super().assign_pool_results(rng, configuration, patches, pool_results)
