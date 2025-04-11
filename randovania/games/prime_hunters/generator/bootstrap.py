from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_boss_location(node: PickupNode, config: HuntersConfiguration) -> bool:
    octolith = node.extra.get("entity_type_data", {}).get("model_id")
    if octolith is not None and octolith == 8 and config.octoliths.prefer_bosses:
        return True

    return False


class HuntersBootstrap(Bootstrap[HuntersConfiguration]):
    def create_damage_state(self, game: GameDescription, configuration: HuntersConfiguration) -> DamageState:
        return EnergyTankDamageState(
            99,
            100,
            game.resource_database,
            game.region_list,
        )

    def assign_pool_results(
        self, rng: Random, configuration: HuntersConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_boss_location)
        self.pre_place_pickups(rng, locations, pool_results, "octolith", patches.game.game)

        return super().assign_pool_results(rng, configuration, patches, pool_results)

    def apply_game_specific_patches(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches
    ) -> None:
        force_fields = patches.game_specific["force_fields"]

        for node in game.region_list.iterate_nodes_of_type(ConfigurableNode):
            requirement = LayoutForceFieldRequirement(force_fields[node.identifier.as_string])
            force_field = game.resource_database.get_item(requirement.item_name)
            game.region_list.configurable_nodes[node.identifier] = ResourceRequirement.simple(force_field)
