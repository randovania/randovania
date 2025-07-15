from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime1.patcher import prime_items
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode


def add_artifacts(
    resource_database: ResourceDatabaseView,
    pickup_database: PickupDatabase,
    total: LayoutArtifactMode,
    artifact_minimum_progression: int,
) -> PoolResults:
    """
    :param resource_database:
    :param pickup_database:
    :param total
    :param artifact_minimum_progression
    :return:
    """
    item_pool: list[PickupEntry] = []

    artifacts_to_place = total.value

    for i in range(artifacts_to_place):
        item_pool.append(
            create_generated_pickup(
                "Chozo Artifact",
                resource_database,
                pickup_database,
                name=prime_items.ARTIFACT_ITEMS[i],
                minimum_progression=artifact_minimum_progression,
            )
        )

    first_automatic_artifact = artifacts_to_place

    starting = [
        create_generated_pickup(
            "Chozo Artifact",
            resource_database,
            pickup_database,
            name=prime_items.ARTIFACT_ITEMS[automatic_artifact],
            minimum_progression=artifact_minimum_progression,
        )
        for automatic_artifact in range(first_automatic_artifact, 12)
    ]

    return PoolResults(item_pool, {}, starting)
