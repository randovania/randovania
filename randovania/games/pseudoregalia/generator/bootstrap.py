from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.pseudoregalia.layout import PseudoregaliaConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.resolver.damage_state import DamageState


class PseudoregaliaBootstrap(Bootstrap[PseudoregaliaConfiguration]):
    def create_damage_state(self, game: GameDescription, configuration: PseudoregaliaConfiguration) -> DamageState:
        return EnergyTankDamageState(100, 100, game.get_resource_database_view().get_item("HealthPiece"))
