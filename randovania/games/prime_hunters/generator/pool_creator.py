from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, HuntersConfiguration)

    # Add Alimbic Artifacts to the item pool
    results.extend_with(add_alimbic_artifacts(game.resource_database))

    # Add Octoliths to the item pool
    results.extend_with(add_octoliths(game, configuration.octoliths))


def add_alimbic_artifacts(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for region in ("Celestial", "Alinos", "Arcterra", "VDO"):
        for artifact_type in ("Attameter", "Cartograph", "Binary Subscripture"):
            for i in range(2):
                artifact = f"{region} {artifact_type} Artifact"
                item_pool.append(create_generated_pickup(artifact, resource_database, i=i + 1))

    return PoolResults(item_pool, {}, [])


def add_octoliths(
    game: GameDescription,
    config: HuntersOctolithConfig,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    octoliths: list[PickupEntry] = [
        create_generated_pickup("Octolith", game.resource_database, i=i + 1) for i in range(8)
    ]

    octoliths_to_shuffle = octoliths[: config.placed_octoliths]
    starting_octoliths = octoliths[config.placed_octoliths :]

    return PoolResults(octoliths_to_shuffle, {}, starting_octoliths)
