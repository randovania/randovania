from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.planets_zebeth.layout import PlanetsZebethConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState

# TODO: look at this later and figure out what to add here


class PlanetsZebethBootstrap(Bootstrap[PlanetsZebethConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: BaseConfiguration) -> DamageState:
        assert isinstance(configuration, PlanetsZebethConfiguration)
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("Energy Tank"),
            [],
        )

    def _get_enabled_misc_resources(
        self, configuration: PlanetsZebethConfiguration, resource_database: ResourceDatabaseView
    ) -> set[str]:
        enabled_resources = set()

        logical_patches = {
            "open_missile_doors_with_one_missile": "OpenMissileDoorWithOneMissile",
        }

        for name, index in logical_patches.items():
            if getattr(configuration, name):
                enabled_resources.add(index)

        return enabled_resources
