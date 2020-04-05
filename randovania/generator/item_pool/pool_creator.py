from typing import Tuple, List

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.generator import base_patches_factory
from randovania.generator.filler.runner import PlayerPool
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.ammo import add_ammo
from randovania.generator.item_pool.dark_temple_keys import add_dark_temple_keys
from randovania.generator.item_pool.major_items import add_major_items
from randovania.generator.item_pool.sky_temple_keys import add_sky_temple_key_distribution_logic
from randovania.layout.layout_configuration import LayoutConfiguration


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results.pickups.extend(extension.pickups)
    base_results.assignment.update(extension.assignment)
    add_resources_into_another(base_results.initial_resources, extension.initial_resources)


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
    base_results = PoolResults([], {}, {})

    # Adding major items to the pool
    _extend_pool_results(base_results, add_major_items(resource_database,
                                                       layout_configuration.major_items_configuration,
                                                       layout_configuration.ammo_configuration))

    # Adding ammo to the pool
    base_results.pickups.extend(add_ammo(resource_database,
                                         layout_configuration.ammo_configuration,
                                         layout_configuration.major_items_configuration.calculate_provided_ammo()))

    # Adding Dark Temple Keys to pool
    _extend_pool_results(base_results, add_dark_temple_keys(resource_database))

    # Adding Sky Temple Keys to pool
    _extend_pool_results(base_results,
                         add_sky_temple_key_distribution_logic(resource_database,
                                                               layout_configuration.sky_temple_keys))

    return base_results
