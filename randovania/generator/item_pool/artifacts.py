from typing import List

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool import PoolResults, pickup_creator


def add_artifacts(resource_database: ResourceDatabase,
                     ) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: List[PickupEntry] = []

    for i in range(12):
        item_pool.append(pickup_creator.create_artifact(i, resource_database))

    return PoolResults(item_pool, {}, {})
