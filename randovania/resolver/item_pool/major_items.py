from typing import Tuple, Dict, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources import PickupEntry, PickupAssignment, ResourceQuantity
from randovania.layout.major_items_configuration import MajorItemsConfiguration
from randovania.resolver.exceptions import InvalidConfiguration
from randovania.resolver.item_pool.pickup_creator import create_major_item, create_energy_tank
from randovania.resolver.item_pool import PoolResults


def add_major_items(game: GameDescription,
                    major_items_configuration: MajorItemsConfiguration,
                    ) -> Tuple[PoolResults, Dict[int, int]]:
    """

    :param game:
    :param major_items_configuration:
    :return:
    """

    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []
    included_ammo_for_item = {}

    for item, state in major_items_configuration.items_state.items():
        if len(item.ammo_index) != len(state.included_ammo):
            raise InvalidConfiguration(
                "Item {0.name} uses {0.ammo} as ammo, but there's only {1} values in included_ammo".format(
                    item, len(state.included_ammo)))

        total_pickups = 0

        if state.include_copy_in_original_location:
            if item.original_index is None:
                raise InvalidConfiguration(
                    "Item {0.name} does not exist in the original game, cannot use state {1}".format(item, state),
                )
            new_assignment[item.original_index] = create_major_item(item, state, True, game.resource_database)
            total_pickups += 1

        for _ in range(state.num_shuffled_pickups):
            item_pool.append(create_major_item(item, state, True, game.resource_database))
            total_pickups += 1

        for _ in range(state.num_included_in_starting_items):
            initial_resources.extend(create_major_item(item, state, False, game.resource_database).resources)
            total_pickups += 1

        for ammo_index, ammo_count in zip(item.ammo_index, state.included_ammo):
            included_ammo_for_item[ammo_index] = included_ammo_for_item.get(ammo_index, 0) + ammo_count * total_pickups

    return (item_pool, new_assignment, initial_resources), included_ammo_for_item


def _add_energy_tanks(game: GameDescription) -> PoolResults:
    total_energy_tanks = 14
    starting_energy_tanks = 0

    item_pool = [
        create_energy_tank(True, game.resource_database)
        for _ in range(total_energy_tanks - starting_energy_tanks)
    ]

    initial_resources = []
    for _ in range(starting_energy_tanks):
        initial_resources.extend(create_energy_tank(False, game.resource_database).resources)

    return item_pool, {}, initial_resources
