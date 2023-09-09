from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_standard_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.ammo_pickup_configuration import AmmoPickupConfiguration
    from randovania.layout.base.standard_pickup_configuration import StandardPickupConfiguration


def _find_ammo_for(ammo_names: tuple[str, ...],
                   ammo_pickup_configuration: AmmoPickupConfiguration,
                   ) -> tuple[AmmoPickupDefinition | None, bool]:
    for ammo, ammo_state in ammo_pickup_configuration.pickups_state.items():
        if ammo.items == ammo_names:
            return ammo, ammo_state.requires_main_item

    return None, False


def add_standard_pickups(resource_database: ResourceDatabase,
                    standard_pickup_configuration: StandardPickupConfiguration,
                    ammo_pickup_configuration: AmmoPickupConfiguration,
                    ) -> PoolResults:
    """

    :param resource_database:
    :param standard_pickup_configuration:
    :param ammo_pickup_configuration:
    :return:
    """

    item_pool: list[PickupEntry] = []
    new_assignment: dict[PickupIndex, PickupEntry] = {}
    starting = []

    for pickup, state in standard_pickup_configuration.pickups_state.items():
        if len(pickup.ammo) != len(state.included_ammo):
            raise InvalidConfiguration(
                "Item {0.name} uses {0.ammo_index} as ammo, but there's only {1} values in included_ammo".format(
                    pickup, len(state.included_ammo)))

        ammo, locked_ammo = _find_ammo_for(pickup.ammo, ammo_pickup_configuration)

        if state.include_copy_in_original_location:
            if pickup.original_location is None:
                raise InvalidConfiguration(
                    f"Item {pickup.name} does not exist in the original game, cannot use state {state}",
                )
            new_assignment[pickup.original_location] = create_standard_pickup(pickup, state, resource_database, ammo,
                                                                              locked_ammo)

        for _ in range(state.num_shuffled_pickups):
            item_pool.append(create_standard_pickup(pickup, state, resource_database, ammo, locked_ammo))

        for _ in range(state.num_included_in_starting_pickups):
            starting.append(create_standard_pickup(pickup, state, resource_database, ammo, locked_ammo))

    return PoolResults(item_pool, new_assignment, starting)
