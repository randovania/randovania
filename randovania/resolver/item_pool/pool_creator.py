from typing import Tuple, List

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import PickupEntry, ResourceDatabase
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.item_pool import PoolResults
from randovania.resolver.item_pool.ammo import add_ammo
from randovania.resolver.item_pool.dark_temple_keys import add_dark_temple_keys
from randovania.resolver.item_pool.major_items import add_major_items
from randovania.resolver.item_pool.sky_temple_keys import add_sky_temple_key_distribution_logic


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results[0].extend(extension[0])
    base_results[1].update(extension[1])
    base_results[2].extend(extension[2])


def calculate_pool_results(layout_configuration: LayoutConfiguration,
                           resource_database: ResourceDatabase,
                           ) -> PoolResults:
    """
    Creates a PoolResults with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param layout_configuration:
    :param resource_database:
    :return:
    """
    base_results = ([], {}, [])

    # Adding major items to the pool
    _extend_pool_results(base_results, add_major_items(resource_database,
                                                       layout_configuration.major_items_configuration))

    # Adding ammo to the pool
    base_results[0].extend(add_ammo(resource_database,
                                    layout_configuration.ammo_configuration,
                                    layout_configuration.major_items_configuration.calculate_provided_ammo()))

    # Adding Dark Temple Keys to pool
    _extend_pool_results(base_results, add_dark_temple_keys(resource_database))

    # Adding Sky Temple Keys to pool
    _extend_pool_results(base_results,
                         add_sky_temple_key_distribution_logic(resource_database,
                                                               layout_configuration.sky_temple_keys))

    return base_results


def calculate_item_pool(layout_configuration: LayoutConfiguration,
                        resource_database: ResourceDatabase,
                        patches: GamePatches,
                        ) -> Tuple[GamePatches, List[PickupEntry]]:
    """
    Creates a GamePatches with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param layout_configuration:
    :param resource_database:
    :param patches:
    :return:
    """

    item_pool, pickup_assignment, initial_items = calculate_pool_results(layout_configuration, resource_database)
    new_patches = patches.assign_pickup_assignment(pickup_assignment).assign_extra_initial_items(initial_items)
    return new_patches, item_pool
