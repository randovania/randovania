from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import (
    PlanetsZebethArtifactConfig,
    PlanetsZebethConfiguration,
)
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, PlanetsZebethConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: PlanetsZebethArtifactConfig) -> PoolResults:
    keys: list[PickupEntry] = [
        create_generated_pickup("Tourian Key", game.resource_database, i=i + 1) for i in range(9)
    ]

    # Check if we have vanilla tourian keys checked
    if config.vanilla_tourian_keys:
        return PoolResults([], {PickupIndex(38): keys[0], PickupIndex(40): keys[1]}, keys[2:])

    # Check whether we have valid artifact requirements in configuration
    if config.required_artifacts > 9:
        raise InvalidConfiguration("More Tourian Keys than allowed!")

    keys_to_shuffle = keys[: config.required_artifacts]
    starting_keys = keys[config.required_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
