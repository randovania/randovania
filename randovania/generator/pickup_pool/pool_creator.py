from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.location_category import LocationCategory
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.ammo_pickup import add_ammo_pickups
from randovania.generator.pickup_pool.standard_pickup import add_standard_pickups
from randovania.layout import filtered_database

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.layout.base.base_configuration import BaseConfiguration


def calculate_pool_results(layout_configuration: BaseConfiguration, game: GameDescription) -> PoolResults:
    """
    Creates a PoolResults with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param layout_configuration:
    :param game:
    :return:
    """
    base_results = PoolResults([], {}, [])

    # Adding standard pickups to the pool
    base_results.extend_with(
        add_standard_pickups(
            game.resource_database,
            layout_configuration.standard_pickup_configuration,
            layout_configuration.ammo_pickup_configuration,
        )
    )

    # Adding ammo to the pool
    base_results.to_place.extend(
        add_ammo_pickups(game.resource_database, layout_configuration.ammo_pickup_configuration)
    )

    # Add game-specific entries to the pool
    layout_configuration.game.generator.pickup_pool_creator(base_results, layout_configuration, game)

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

    result: dict[LocationCategory | str, list[int]] = {cat: [0, 0] for cat in LocationCategory}

    for node in game_description.region_list.iterate_nodes():
        if isinstance(node, PickupNode):
            result[node.location_category][1] += 1

    pool_results = calculate_pool_results(layout, game_description)
    result["Starting"] = [0, layout.standard_pickup_configuration.minimum_random_starting_pickups]

    all_pickups = pool_results.to_place + list(pool_results.assignment.values())
    for pickup in all_pickups:
        result[pickup.generator_params.preferred_location_category][0] += 1

    return {key: PoolCount(*value) for key, value in result.items()}


def get_total_pickup_count(sizes: dict[LocationCategory | str, PoolCount]) -> PoolCount:
    """
    Merges the result of calculate_pool_pickup_count into a global count that doesn't care about the categories.
    """
    pickups, nodes = 0, 0
    for a, b in sizes.values():
        pickups += a
        nodes += b
    return PoolCount(pickups, nodes)
