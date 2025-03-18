from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersConfiguration
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


def add_alimbic_artifacts(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for region in ("Celestial Archives", "Alinos", "Arcterra", "Vesper Defense Outpost"):
        for artifact_type in ("Attameter", "Cartograph", "Binary Subscripture"):
            for i in range(1, 4):
                artifact = f"{region} {artifact_type} Artifact {i}"
                item_pool.append(create_generated_pickup(artifact, resource_database, i=i + 1))

    return PoolResults(item_pool, {}, [])
