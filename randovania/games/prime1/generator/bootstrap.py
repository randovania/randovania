from __future__ import annotations

import copy
import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_reduction import DamageReduction
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.prime1.layout.prime_configuration import DamageReduction as DamageReductionConfig
from randovania.games.prime1.layout.prime_configuration import IngameDifficulty, PrimeConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration


class PrimeBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(
        self, configuration: BaseConfiguration, resource_database: ResourceDatabase
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
        }
        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        if configuration.dock_rando.is_enabled():
            enabled_resources.add("dock_rando")

        if configuration.ingame_difficulty == IngameDifficulty.HARD:
            enabled_resources.add("hard_mode")

        return enabled_resources

    def prime1_progressive_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(
            current_resources[db.get_item_by_name(suit)] for suit in ["Varia Suit", "Gravity Suit", "Phazon Suit"]
        )
        if num_suits >= 3:
            dr = 0.5
        elif num_suits == 2:
            dr = 0.8
        elif num_suits == 1:
            dr = 0.9
        else:
            dr = 1

        hard_mode = db.get_by_type_and_index(ResourceType.MISC, "hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def prime1_additive_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection) -> float:
        dr = 1.0
        if current_resources[db.get_item_by_name("Varia Suit")]:
            dr -= 0.1
        if current_resources[db.get_item_by_name("Gravity Suit")]:
            dr -= 0.1
        if current_resources[db.get_item_by_name("Phazon Suit")]:
            dr -= 0.3

        hard_mode = db.get_by_type_and_index(ResourceType.MISC, "hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def prime1_absolute_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        if current_resources[db.get_item_by_name("Phazon Suit")] > 0:
            dr = 0.5
        elif current_resources[db.get_item_by_name("Gravity Suit")] > 0:
            dr = 0.8
        elif current_resources[db.get_item_by_name("Varia Suit")] > 0:
            dr = 0.9
        else:
            dr = 1

        hard_mode = db.get_by_type_and_index(ResourceType.MISC, "hard_mode")
        if current_resources.has_resource(hard_mode):
            dr *= 1.53

        return dr

    def patch_resource_database(self, db: ResourceDatabase, configuration: BaseConfiguration) -> ResourceDatabase:
        assert isinstance(configuration, PrimeConfiguration)

        base_damage_reduction = db.base_damage_reduction
        damage_reductions = copy.copy(db.damage_reductions)
        requirement_template = copy.copy(db.requirement_template)

        suits = [db.get_item_by_name("Varia Suit")]
        if not configuration.legacy_mode:
            requirement_template["Heat-Resisting Suit"] = dataclasses.replace(
                requirement_template["Heat-Resisting Suit"],
                requirement=ResourceRequirement.simple(db.get_item_by_name("Varia Suit")),
            )
        else:
            suits.extend([db.get_item_by_name("Gravity Suit"), db.get_item_by_name("Phazon Suit")])

        reductions = [DamageReduction(None, configuration.heat_damage / 10.0)]
        reductions.extend([DamageReduction(suit, 0) for suit in suits])
        damage_reductions[db.get_by_type_and_index(ResourceType.DAMAGE, "HeatDamage1")] = reductions

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
