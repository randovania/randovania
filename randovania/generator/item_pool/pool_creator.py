from random import Random
from typing import Tuple

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.ammo import add_ammo
from randovania.generator.item_pool.major_items import add_major_items
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results.pickups.extend(extension.pickups)
    base_results.assignment.update(extension.assignment)
    base_results.initial_resources.add_resource_gain(extension.initial_resources.as_resource_gain())


def calculate_pool_results(layout_configuration: BaseConfiguration,
                           resource_database: ResourceDatabase,
                           base_patches: GamePatches = None,
                           rng: Random = None,
                           rng_required: bool = False
                           ) -> PoolResults:
    """
    Creates a PoolResults with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param layout_configuration:
    :param resource_database:
    :return:
    """
    base_results = PoolResults([], {}, ResourceCollection.with_database(resource_database))

    # Adding major items to the pool
    _extend_pool_results(base_results, add_major_items(resource_database,
                                                       layout_configuration.major_items_configuration,
                                                       layout_configuration.ammo_configuration))

    # Adding ammo to the pool
    base_results.pickups.extend(add_ammo(resource_database,
                                         layout_configuration.ammo_configuration))
    try:
        layout_configuration.game.generator.item_pool_creator(
            base_results, layout_configuration, resource_database, base_patches, rng,
        )
    except MissingRng as e:
        if rng_required:
            raise e

    return base_results


def calculate_pool_item_count(layout: BaseConfiguration) -> Tuple[int, int]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there.
    :param layout:
    :return:
    """
    game_description = filtered_database.game_description_for_layout(layout)

    num_pickup_nodes = game_description.world_list.num_pickup_nodes
    pool_results = calculate_pool_results(layout, game_description.resource_database,
                                          rng_required=False)
    min_starting_items = layout.major_items_configuration.minimum_random_starting_items

    pool_count = len(pool_results.pickups) + len(pool_results.assignment)
    maximum_size = num_pickup_nodes + min_starting_items

    return pool_count, maximum_size
