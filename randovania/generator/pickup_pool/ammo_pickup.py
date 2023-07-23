from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.pickup_pool.pickup_creator import create_ammo_pickup

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.resources.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration


def add_ammo_pickups(resource_database: ResourceDatabase,
             ammo_configuration: AmmoPickupConfiguration,
             ) -> Iterator[PickupEntry]:
    """
    Creates the necessary pickups for the given ammo_configuration.
    :param resource_database:
    :param ammo_configuration:
    :return:
    """
    for ammo, state in ammo_configuration.pickups_state.items():
        for _ in range(state.pickup_count):
            yield create_ammo_pickup(ammo, state.ammo_count, state.requires_main_item, resource_database)
