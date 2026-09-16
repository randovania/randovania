from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_origins.layout import MPOConfiguration
from randovania.resolver.bootstrap import Bootstrap
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.resolver.damage_state import DamageState


class MPOBootstrap(Bootstrap[MPOConfiguration]):
    def create_damage_state(self, game: GameDatabaseView, configuration: MPOConfiguration) -> DamageState:
        db = game.get_resource_database_view()
        return EnergyTankDamageState(
            100,
            100,
            db.get_item("EnergyTank"),
            [db.get_item(suit) for suit in ["VariaSuit", "GravitySuit", "PhazonSuit"]],
        )

    def _get_enabled_misc_resources(self, configuration, resource_database):
        enabled_resources = set()

        if configuration.main_bosses_required:
            enabled_resources.add("GameModeRemix")
        return enabled_resources
