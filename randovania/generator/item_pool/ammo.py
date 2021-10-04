from typing import Iterator

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool.pickup_creator import create_ammo_expansion
from randovania.layout.base.ammo_configuration import AmmoConfiguration


def add_ammo(resource_database: ResourceDatabase,
             ammo_configuration: AmmoConfiguration,
             ) -> Iterator[PickupEntry]:
    """
    Creates the necessary pickups for the given ammo_configuration.
    :param resource_database:
    :param ammo_configuration:
    :return:
    """
    for ammo, state in ammo_configuration.items_state.items():
        for _ in range(state.pickup_count):
            yield create_ammo_expansion(ammo, state.ammo_count, state.requires_major_item, resource_database)
