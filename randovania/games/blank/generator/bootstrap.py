from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.blank.layout import BlankConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.resolver.damage_state import DamageState


class BlankBootstrap(Bootstrap[BlankConfiguration]):
    def create_damage_state(self, game: GameDescription, configuration: BlankConfiguration) -> DamageState:
        return EnergyTankDamageState(
            100,
            100,
            game.resource_database,
            game.region_list,
        )
