from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.blank.layout import BlankConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.resolver.damage_state import DamageState


class BlankBootstrap(Bootstrap[BlankConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: BlankConfiguration) -> DamageState:
        return EnergyTankDamageState(100, 100, game.get_resource_database_view().get_item("Health"))
