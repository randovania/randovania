from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime1.generator.pickup_pool.artifacts import add_artifacts
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def prime1_specific_pool(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, PrimeConfiguration)
    results.extend_with(
        add_artifacts(
            game.get_resource_database_view(),
            game.get_pickup_database(),
            configuration.artifact_target,
            configuration.artifact_minimum_progression,
        )
    )
