from typing import List

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pickup_creator import create_dark_temple_key


def add_dark_temple_keys(resource_database: ResourceDatabase,
                         ) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: List[PickupEntry] = []

    for temple_index in range(3):
        for i in range(3):
            item_pool.append(create_dark_temple_key(i, temple_index, resource_database))

    return item_pool, {}, {}
