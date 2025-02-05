from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig, DreadConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, DreadConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: DreadArtifactConfig) -> PoolResults:
    keys = [create_generated_pickup("Metroid DNA", game.resource_database, i=i + 1) for i in range(12)]
    keys_to_shuffle = keys[: config.required_artifacts]
    starting_keys = keys[config.required_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
