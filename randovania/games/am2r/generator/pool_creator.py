from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig, AM2RConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, AM2RConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: AM2RArtifactConfig) -> PoolResults:
    # Check whether we have valid artifact requirements in configuration
    max_artifacts = 0
    if config.prefer_anywhere:
        max_artifacts = 46
    elif config.prefer_metroids:
        max_artifacts = 46
    elif config.prefer_bosses:
        max_artifacts = 6
    if config.required_artifacts > max_artifacts:
        raise InvalidConfiguration("More Metroid DNA than allowed!")

    keys: list[PickupEntry] = [
        create_generated_pickup("Metroid DNA", game.resource_database, i=i + 1) for i in range(46)
    ]
    keys_to_shuffle = keys[: config.placed_artifacts]
    starting_keys = keys[config.placed_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
