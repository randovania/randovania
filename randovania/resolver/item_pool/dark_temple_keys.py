from typing import List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import PickupEntry, ResourceDatabase
from randovania.resolver.item_pool.pickup_creator import create_dark_temple_key
from randovania.resolver.item_pool import PoolResults


def add_dark_temple_keys(resource_database: ResourceDatabase,
                         ) -> PoolResults:
    """
    :param game:
    :return:
    """
    item_pool: List[PickupEntry] = []

    for temple_index in range(3):
        for i in range(3):
            item_pool.append(create_dark_temple_key(i, temple_index, resource_database))

    return item_pool, {}, []
