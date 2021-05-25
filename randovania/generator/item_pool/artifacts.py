from typing import List

from randovania.game_description.resources import resource_info
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.generator.item_pool import PoolResults, pickup_creator
from randovania.layout.prime1.artifact_mode import LayoutArtifactMode


def add_artifacts(resource_database: ResourceDatabase,
                  mode: LayoutArtifactMode,
                  ) -> PoolResults:
    """
    :param resource_database:
    :param mode
    :return:
    """
    item_pool: List[PickupEntry] = []
    initial_resources: CurrentResources = {}

    artifacts_to_place = mode.value

    for i in range(artifacts_to_place):
        item_pool.append(pickup_creator.create_artifact(i, resource_database))

    first_automatic_artifact = artifacts_to_place

    for automatic_artifact in range(first_automatic_artifact, 12):
        resource_info.add_resource_gain_to_current_resources(
            pickup_creator.create_artifact(automatic_artifact, resource_database).all_resources,
            initial_resources
        )

    return PoolResults(item_pool, {}, initial_resources)

