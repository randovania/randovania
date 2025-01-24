from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase


def add_energy_cells(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for i in range(9):
        item_pool.append(create_generated_pickup("Energy Cell", resource_database, i=i + 1))

    return PoolResults(item_pool, {}, [])
