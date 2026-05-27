from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.zero_mission.layout import MZMConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.resolver.damage_state import DamageState


class MZMBootstrap(Bootstrap[MZMConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: MZMConfiguration) -> DamageState:
        return EnergyTankDamageState(
            configuration.energy_per_tank - 1,
            configuration.energy_per_tank,
            game.get_resource_database_view().get_item("EnergyTank"),
            [
                game.get_resource_database_view().get_item("VariaSuit"),
                game.get_resource_database_view().get_item("GravitySuit"),
            ],
        )
