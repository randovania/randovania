from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.planets_zebeth.layout import PlanetsZebethConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.damage_state import DamageState, EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration

# TODO: look at this later and figure out what to add here


class PlanetsZebethBootstrap(Bootstrap):
    def create_damage_state(self, game: GameDescription, configuration: BaseConfiguration) -> DamageState:
        assert isinstance(configuration, PlanetsZebethConfiguration)
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.resource_database,
            game.region_list,
        )
