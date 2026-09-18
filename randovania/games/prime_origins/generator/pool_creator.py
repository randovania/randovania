from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_origins.layout.prime_origins_configuration import MPOConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration

from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode


ARTIFACTS = [
    "Truth",
    "Strength",
    "Elder",
    "Wild",
    "Lifegiver",
    "Warrior",
    "Chozo",
    "Nature",
    "Sun",
    "World",
    "Spirit",
    "Newborn",
]


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, MPOConfiguration)
    results.extend_with(
        add_artifacts(
            game.get_resource_database_view(),
            game.get_pickup_database(),
            configuration.artifact_target,
            configuration.artifact_minimum_progression,
        )
    )


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

    for i in range(total):
        item_pool.append(
            create_generated_pickup(
                "Chozo Artifact",
                resource_database,
                pickup_database,
                name=ARTIFACTS[i],
                minimum_progression=artifact_minimum_progression,
            )
        )

    starting = [
        create_generated_pickup(
            "Chozo Artifact",
            resource_database,
            pickup_database,
            name=ARTIFACTS[automatic_artifact],
            minimum_progression=artifact_minimum_progression,
        )
        for automatic_artifact in range(total, 12)
    ]

    return PoolResults(item_pool, {}, starting)
