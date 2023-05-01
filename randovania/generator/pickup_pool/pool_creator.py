from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.world.pickup_node import PickupNode
from randovania.generator.base_patches_factory import MissingRng
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.ammo_pickup import add_ammo_pickups
from randovania.generator.pickup_pool.standard_pickup import add_standard_pickups
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import BaseConfiguration


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results.to_place.extend(extension.to_place)
    base_results.assignment.update(extension.assignment)
    base_results.starting.extend(extension.starting)


def calculate_pool_results(layout_configuration: BaseConfiguration,
                           game: GameDescription,
                           base_patches: GamePatches = None,
                           rng: Random = None,
                           rng_required: bool = False
                           ) -> PoolResults:
    """
    Creates a PoolResults with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param layout_configuration:
    :param game:
    :param base_patches
    :param rng:
    :param rng_required
    :return:
    """
    base_results = PoolResults([], {}, [])

    # Adding standard pickups to the pool
    _extend_pool_results(base_results, add_standard_pickups(game.resource_database,
                                                       layout_configuration.standard_pickup_configuration,
                                                       layout_configuration.ammo_pickup_configuration))

    # Adding ammo to the pool
    base_results.to_place.extend(add_ammo_pickups(game.resource_database,
                                          layout_configuration.ammo_pickup_configuration))
    try:
        layout_configuration.game.generator.item_pool_creator(
            base_results, layout_configuration, game, base_patches, rng,
        )
    except MissingRng:
        if rng_required:
            raise

    return base_results


def calculate_pool_pickup_count(layout: BaseConfiguration) -> tuple[int, int]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there.
    :param layout:
    :return:
    """
    game_description = filtered_database.game_description_for_layout(layout)

    num_pickup_nodes = game_description.world_list.num_pickup_nodes
    pool_results = calculate_pool_results(layout, game_description,
                                          rng_required=False)
    min_starting_pickups = layout.standard_pickup_configuration.minimum_random_starting_pickups

    pool_count = len(pool_results.to_place) + len(pool_results.assignment)
    maximum_size = num_pickup_nodes + min_starting_pickups

    return pool_count, maximum_size


def calculate_split_pool_pickup_count(layout: BaseConfiguration) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there. Split by major/minor.
    :param layout:
    :return:
    """
    game_description = filtered_database.game_description_for_layout(layout)

    pickup_nodes = [node for node in game_description.world_list.iterate_nodes()
                    if isinstance(node, PickupNode)]
    num_major_nodes = sum(1 for node in pickup_nodes if node.location_category == LocationCategory.MAJOR)
    num_minor_nodes = len(pickup_nodes) - num_major_nodes

    pool_results = calculate_pool_results(layout, game_description,
                                          rng_required=False)
    all_pickups = pool_results.to_place + list(pool_results.assignment.values())
    minor_count = sum(1 for pickup in all_pickups
                      if pickup.generator_params.preferred_location_category == LocationCategory.MINOR)
    major_count = len(all_pickups) - minor_count

    return (major_count, num_major_nodes), (minor_count, num_minor_nodes)
