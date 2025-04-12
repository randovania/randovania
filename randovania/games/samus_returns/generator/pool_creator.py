from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, MSRConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDatabaseView, config: MSRArtifactConfig) -> PoolResults:
    # Check whether we have valid artifact requirements in configuration
    max_artifacts = 0
    if config.prefer_anywhere:
        max_artifacts = 39
    if config.prefer_metroids:
        max_artifacts += 24
    if config.prefer_stronger_metroids:
        max_artifacts += 15
    if config.prefer_bosses and max_artifacts < 36:
        max_artifacts += 4
    if config.required_artifacts > max_artifacts:
        raise InvalidConfiguration("More Metroid DNA than allowed!")

    keys: list[PickupEntry] = [
        create_generated_pickup("Metroid DNA", game.get_resource_database_view(), game.get_pickup_database(), i=i + 1)
        for i in range(39)
    ]
    keys_to_shuffle = keys[: config.placed_artifacts]
    starting_keys = keys[config.placed_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
