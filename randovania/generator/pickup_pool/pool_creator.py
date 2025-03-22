from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.filtered_game_database_view import LayerFilteredGameDatabaseView
from randovania.game_description.resources.location_category import LocationCategory
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.ammo_pickup import add_ammo_pickups
from randovania.generator.pickup_pool.standard_pickup import add_standard_pickups

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.layout.base.base_configuration import BaseConfiguration


def calculate_pool_results(configuration: BaseConfiguration, game: GameDatabaseView) -> PoolResults:
    """
    Creates a PoolResults with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param configuration:
    :param game:
    :return:
    """
    base_results = PoolResults([], {}, [])

    # Adding standard pickups to the pool
    base_results.extend_with(
        add_standard_pickups(
            game.get_resource_database_view(),
            configuration.standard_pickup_configuration,
            configuration.ammo_pickup_configuration,
        )
    )

    # Adding ammo to the pool
    base_results.to_place.extend(
        add_ammo_pickups(game.get_resource_database_view(), configuration.ammo_pickup_configuration)
    )

    # Add game-specific entries to the pool
    configuration.game.generator.pickup_pool_creator(base_results, configuration, game)

    return base_results


class PoolCount(NamedTuple):
    pickups: int
    locations: int


def calculate_pool_pickup_count(configuration: BaseConfiguration) -> dict[LocationCategory | str, PoolCount]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there.
    :param configuration:
    :return:
    """

    view = LayerFilteredGameDatabaseView.create_for_configuration(
        configuration.game_enum().game_description,
        configuration,
    )

    result: dict[LocationCategory | str, list[int]] = {cat: [0, 0] for cat in LocationCategory}

    for _, _, node in view.iterate_nodes_of_type(PickupNode):
        result[node.location_category][1] += 1

    pool_results = calculate_pool_results(configuration, view)
    result["Starting"] = [0, configuration.standard_pickup_configuration.minimum_random_starting_pickups]

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
