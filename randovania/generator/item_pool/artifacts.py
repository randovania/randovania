from typing import List

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool import PoolResults, pickup_creator
from randovania.layout.prime1.artifact_mode import LayoutArtifactMode


def add_artifacts(resource_database: ResourceDatabase,
                  artifacts: LayoutArtifactMode,
                  ) -> PoolResults:
    """
    :param resource_database:
    :param artifacts
    :return:
    """
    item_pool: List[PickupEntry] = []

    for i in range(artifacts.num_artifacts):
        item_pool.append(pickup_creator.create_artifact(i, resource_database))

    return PoolResults(item_pool, {}, {})
