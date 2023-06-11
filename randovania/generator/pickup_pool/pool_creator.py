from random import Random
from typing import NamedTuple

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.db.pickup_node import PickupNode
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


class PoolCount(NamedTuple):
    pickups: int
    locations: int


def calculate_pool_pickup_count(layout: BaseConfiguration) -> dict[LocationCategory | str, PoolCount]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there.
    :param layout:
    :return:
    """
    game_description = filtered_database.game_description_for_layout(layout)

    result = {
        cat: [0, 0]
        for cat in LocationCategory
    }

    for node in game_description.region_list.iterate_nodes():
        if isinstance(node, PickupNode):
            result[node.location_category][1] += 1

    pool_results = calculate_pool_results(layout, game_description,
                                          rng_required=False)
    result["Starting"] = [0, layout.standard_pickup_configuration.minimum_random_starting_pickups]

    all_pickups = pool_results.to_place + list(pool_results.assignment.values())
    for pickup in all_pickups:
        result[pickup.generator_params.preferred_location_category][0] += 1

    return {
        key: PoolCount(*value)
        for key, value in result.items()
    }


def get_total_pickup_count(sizes: dict[LocationCategory | str, PoolCount]) -> PoolCount:
    """
    Merges the result of calculate_pool_pickup_count into a global count that doesn't care about the categories.
    """
    pickups, nodes = 0, 0
    for a, b in sizes.values():
        pickups += a
        nodes += b
    return PoolCount(pickups, nodes)
