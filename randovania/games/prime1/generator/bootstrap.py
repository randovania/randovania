import copy
import dataclasses

from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.damage_resource_info import DamageReduction
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver.bootstrap import MetroidBootstrap


class PrimeBootstrap(MetroidBootstrap):
    def _get_enabled_misc_resources(self, configuration: BaseConfiguration,
                                    resource_database: ResourceDatabase) -> set[str]:
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

        return enabled_resources

    def prime1_progressive_damage_reduction(self, db: ResourceDatabase, current_resources: ResourceCollection):
        num_suits = sum(current_resources[db.get_item_by_name(suit)]
                        for suit in ["Varia Suit", "Gravity Suit", "Phazon Suit"])
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
        if configuration.heat_protection_only_varia:
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

        return dataclasses.replace(db, damage_reductions=damage_reductions, base_damage_reduction=base_damage_reduction,
                                   requirement_template=requirement_template)
