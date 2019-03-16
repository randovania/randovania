from typing import List

from randovania.game_description.resources import PickupEntry, PickupAssignment, ResourceQuantity, PickupIndex, \
    ResourceDatabase
from randovania.layout.layout_configuration import LayoutSkyTempleKeyMode
from randovania.resolver.exceptions import InvalidConfiguration
from randovania.resolver.item_pool import PoolResults
from randovania.resolver.item_pool.pickup_creator import create_sky_temple_key


def add_sky_temple_key_distribution_logic(resource_database: ResourceDatabase,
                                          mode: LayoutSkyTempleKeyMode,
                                          ) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :param resource_database:
    :param mode:
    :return:
    """

    item_pool: List[PickupEntry] = []
    new_assignment: PickupAssignment = {}
    initial_resources: List[ResourceQuantity] = []

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        locations_to_place = _GUARDIAN_INDICES[:]
        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            locations_to_place += _SUB_GUARDIAN_INDICES

        for key_number, location in enumerate(locations_to_place):
            new_assignment[location] = create_sky_temple_key(key_number, resource_database)
        first_automatic_key = len(locations_to_place)

    else:
        keys_to_place = mode.value
        if not isinstance(keys_to_place, int):
            raise InvalidConfiguration("Unknown Sky Temple Key mode: {}".format(mode))

        for key_number in range(keys_to_place):
            item_pool.append(create_sky_temple_key(key_number, resource_database))
        first_automatic_key = keys_to_place

    for automatic_key_number in range(first_automatic_key, 9):
        initial_resources.extend(create_sky_temple_key(automatic_key_number, resource_database).all_resources)

    return item_pool, new_assignment, initial_resources


_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]
