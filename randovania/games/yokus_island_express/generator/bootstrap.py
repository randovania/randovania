from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.yokus_island_express.layout import YokuConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.no_op_damage_state import NoOpDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.resolver.damage_state import DamageState


class YokuBootstrap(Bootstrap[YokuConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: YokuConfiguration) -> DamageState:
        return NoOpDamageState()  # Yoku can't take damage
