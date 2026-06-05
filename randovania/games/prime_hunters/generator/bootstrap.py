from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.games.prime_hunters.layout import HuntersConfiguration, force_field_configuration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.lib.json_lib import JsonType
from randovania.resolver.bootstrap import Bootstrap, ConfigurableNodeBootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.pickup_pool import PoolResults
    from randovania.resolver.damage_state import DamageState


def is_boss_location(node: PickupNode, config: HuntersConfiguration) -> bool:
    octolith = node.extra.get("fields", {}).get("model_id")
    if octolith is not None and octolith == 8 and config.octoliths.prefer_bosses:
        return True

    return False


class HuntersBootstrap(Bootstrap[HuntersConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: HuntersConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.starting_energy,
            100,
            game.get_resource_database_view().get_item("EnergyTank"),
            [],
        )

    def assign_pool_results(
        self, rng: Random, configuration: HuntersConfiguration, patches: GamePatches, pool_results: PoolResults
    ) -> GamePatches:
        pickups_to_preplace = [
            pickup for pickup in list(pool_results.to_place) if pickup.gui_category.name == "octolith"
        ]
        locations = self.all_preplaced_pickup_locations(patches.game, configuration, is_boss_location)
        self.pre_place_pickups(rng, pickups_to_preplace, locations, pool_results, patches.game.game)

        return super().assign_pool_results(rng, configuration, patches, pool_results)

    @override
    @classmethod
    def _configurable_node_class(cls) -> type[ConfigurableNodeBootstrap]:
        return ForceFieldBootstrap


class ForceFieldBootstrap(ConfigurableNodeBootstrap[HuntersConfiguration, LayoutForceFieldRequirement]):
    @override
    @property
    def category_name(self) -> str:
        return "Force Fields"

    @override
    def get_options(
        self, configuration: HuntersConfiguration, game: GameDescription, node: ConfigurableNode
    ) -> dict[str, LayoutForceFieldRequirement | None]:
        ff_requirement = configuration.force_field_configuration.force_field_requirement
        node_requirement = ff_requirement[node.identifier]

        return self._get_standard_options(
            node_requirement,
            node_requirement.long_name,
            {LayoutForceFieldRequirement.RANDOM},
            {req.long_name: req for req in force_field_configuration.ITEM_NAMES.keys()},
        )

    @override
    def get_requirement(
        self, configuration: HuntersConfiguration, game: GameDescription, node_config: LayoutForceFieldRequirement
    ) -> Requirement:
        resource_db = game.get_resource_database_view()
        force_field = resource_db.get_item(node_config.item_name)
        return ResourceRequirement.simple(force_field)

    @override
    def get_node_config(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches, node: ConfigurableNode
    ) -> LayoutForceFieldRequirement:
        force_fields = patches.game_specific["force_fields"]
        return LayoutForceFieldRequirement(force_fields[node.identifier.as_string])

    @override
    def get_default_patches(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches
    ) -> GamePatches:
        return patches.assign_game_specific(
            {
                "force_fields": {
                    node.identifier.as_string: LayoutForceFieldRequirement.POWER_BEAM
                    for node in game.region_list.iterate_nodes_of_type(ConfigurableNode)
                }
            }
        )

    @override
    def config_data_to_json(self, value: LayoutForceFieldRequirement) -> JsonType:
        return value.value

    @override
    def json_to_config_data(self, value: JsonType) -> LayoutForceFieldRequirement:
        return LayoutForceFieldRequirement(value)
