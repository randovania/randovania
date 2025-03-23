from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.games.prime_hunters.layout import HuntersConfiguration
from randovania.games.prime_hunters.layout.force_field_configuration import LayoutForceFieldRequirement
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.resolver.damage_state import DamageState


class HuntersBootstrap(Bootstrap[HuntersConfiguration]):
    def create_damage_state(self, game: GameDescription, configuration: HuntersConfiguration) -> DamageState:
        return EnergyTankDamageState(
            100,
            100,
            game.resource_database,
            game.region_list,
        )

    def apply_game_specific_patches(
        self, configuration: HuntersConfiguration, game: GameDescription, patches: GamePatches
    ) -> None:
        force_fields = patches.game_specific["force_fields"]

        for node in game.region_list.iterate_nodes_of_type(ConfigurableNode):
            requirement = LayoutForceFieldRequirement(force_fields[node.identifier.as_string])
            force_field = game.resource_database.get_item(requirement.item_name)
            game.region_list.configurable_nodes[node.identifier] = ResourceRequirement.simple(force_field)
