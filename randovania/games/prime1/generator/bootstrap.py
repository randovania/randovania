from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.prime1.generator.pickup_pool.artifacts import ARTIFACT_CATEGORY
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def all_artifact_locations(game: GameDescription):
    locations = []

    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode):
            locations.append(node)

    return locations


class PrimeBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
    ) -> set[str]:
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
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("dock_rando")

        return enabled_resources

    def prime1_progressive_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(
            current_resources[db.get_item_by_name(suit)] for suit in ["Varia Suit", "Gravity Suit", "Phazon Suit"]
        )
        if num_suits >= 3:
            return 0.5
        elif num_suits == 2:
            return 0.8
        elif num_suits == 1:
            return 0.9
        else:
            return 1

    def prime1_absolute_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        if current_resources[db.get_item_by_name("Phazon Suit")] > 0:
            return 0.5
        elif current_resources[db.get_item_by_name("Gravity Suit")] > 0:
            return 0.8
        elif current_resources[db.get_item_by_name("Varia Suit")] > 0:
            return 0.9
        else:
            return 1

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        base_damage_reduction = db.base_damage_reduction
        damage_reductions = copy.copy(db.damage_reductions)
        requirement_template = copy.copy(db.requirement_template)

        suits = [db.get_item_by_name("Varia Suit")]
        if not configuration.legacy_mode:
            requirement_template["Heat-Resisting Suit"] = ResourceRequirement.simple(db.get_item_by_name("Varia Suit"))
        else:
            suits.extend([db.get_item_by_name("Gravity Suit"), db.get_item_by_name("Phazon Suit")])

        reductions = [DamageReduction(None, configuration.heat_damage / 10.0)]
        reductions.extend([DamageReduction(suit, 0) for suit in suits])
        damage_reductions[db.get_by_type_and_index(ResourceType.DAMAGE, "HeatDamage1")] = reductions

        if configuration.progressive_damage_reduction:
            base_damage_reduction = self.prime1_progressive_damage_reduction
        else:
            base_damage_reduction = self.prime1_absolute_damage_reduction

        return dataclasses.replace(
            db,
            damage_reductions=damage_reductions,
            base_damage_reduction=base_damage_reduction,
            requirement_template=requirement_template,
        )

    def assign_pool_results(self, rng: Random, patches: GamePatches, pool_results: PoolResults) -> GamePatches:
        assert isinstance(patches.configuration, PrimeConfiguration)

        locations = all_artifact_locations(patches.game)
        rng.shuffle(locations)

        artifacts_to_assign = [
            pickup for pickup in list(pool_results.to_place) if pickup.pickup_category is ARTIFACT_CATEGORY
        ]

        if len(artifacts_to_assign) > len(locations):
            raise InvalidConfiguration(
                f"Has {len(artifacts_to_assign)} artifacts in the pool, but only {len(locations)} valid locations."
            )

        for artifact, location in zip(artifacts_to_assign, locations, strict=False):
            pool_results.to_place.remove(artifact)
            pool_results.assignment[location.pickup_index] = artifact

        return super().assign_pool_results(rng, patches, pool_results)
