from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode
from randovania.generator.item_pool import PoolResults, pickup_creator


def add_artifacts(resource_database: ResourceDatabase,
                  mode: LayoutArtifactMode,
                  artifact_minimum_progression: int,
                  ) -> PoolResults:
    """
    :param resource_database:
    :param mode
    :param artifact_minimum_progression
    :return:
    """
    item_pool: list[PickupEntry] = []

    artifacts_to_place = mode.value

    for i in range(artifacts_to_place):
        item_pool.append(pickup_creator.create_artifact(i, artifact_minimum_progression, resource_database))

    first_automatic_artifact = artifacts_to_place

    starting = [
        pickup_creator.create_artifact(automatic_artifact, artifact_minimum_progression, resource_database)
        for automatic_artifact in range(first_automatic_artifact, 12)
    ]

    return PoolResults(item_pool, {}, starting)
