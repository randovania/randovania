from randovania.game_description.pickup.ammo_pickup import AmmoPickupDefinition
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pickup_creator import create_standard_pickup
from randovania.layout.base.ammo_configuration import AmmoConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.exceptions import InvalidConfiguration


def _find_ammo_for(ammo_index: tuple[str, ...],
                   ammo_configuration: AmmoConfiguration,
                   ) -> tuple[AmmoPickupDefinition | None, bool]:
    for ammo, ammo_state in ammo_configuration.items_state.items():
        if ammo.items == ammo_index:
            return ammo, ammo_state.requires_major_item

    return None, False


def add_major_items(resource_database: ResourceDatabase,
                    major_items_configuration: MajorItemsConfiguration,
                    ammo_configuration: AmmoConfiguration,
                    ) -> PoolResults:
    """

    :param resource_database:
    :param major_items_configuration:
    :param ammo_configuration:
    :return:
    """

    item_pool: list[PickupEntry] = []
    new_assignment: dict[PickupIndex, PickupEntry] = {}
    starting = []

    for item, state in major_items_configuration.items_state.items():
        if len(item.ammo) != len(state.included_ammo):
            raise InvalidConfiguration(
                "Item {0.name} uses {0.ammo_index} as ammo, but there's only {1} values in included_ammo".format(
                    item, len(state.included_ammo)))

        ammo, locked_ammo = _find_ammo_for(item.ammo, ammo_configuration)

        if state.include_copy_in_original_location:
            if item.original_location is None:
                raise InvalidConfiguration(
                    f"Item {item.name} does not exist in the original game, cannot use state {state}",
                )
            new_assignment[item.original_location] = create_standard_pickup(item, state, True,
                                                                    resource_database, ammo, locked_ammo)

        for _ in range(state.num_shuffled_pickups):
            item_pool.append(create_standard_pickup(item, state, True, resource_database, ammo, locked_ammo))

        for _ in range(state.num_included_in_starting_items):
            starting.append(create_standard_pickup(item, state, False, resource_database, ammo, locked_ammo))

    return PoolResults(item_pool, new_assignment, starting)
