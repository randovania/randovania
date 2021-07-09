import typing
from typing import Tuple, Callable, Dict

from randovania.game_description import default_database
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.ammo import add_ammo
from randovania.generator.item_pool.artifacts import add_artifacts
from randovania.generator.item_pool.dark_temple_keys import add_dark_temple_keys
from randovania.generator.item_pool.energy_cells import add_energy_cells
from randovania.generator.item_pool.major_items import add_major_items
from randovania.generator.item_pool.sky_temple_keys import add_sky_temple_key_distribution_logic
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.prime3.corruption_configuration import CorruptionConfiguration
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.layout.prime1.prime_configuration import PrimeConfiguration


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results.pickups.extend(extension.pickups)
    base_results.assignment.update(extension.assignment)
    add_resources_into_another(base_results.initial_resources, extension.initial_resources)


def prime1_specific_pool(results: PoolResults, configuration: PrimeConfiguration, db: ResourceDatabase):
    _extend_pool_results(results, add_artifacts(db, configuration.artifacts))


def echoes_specific_pool(results: PoolResults, configuration: EchoesConfiguration, db: ResourceDatabase):
    # Adding Dark Temple Keys to pool
    _extend_pool_results(results, add_dark_temple_keys(db))

    # Adding Sky Temple Keys to pool
    _extend_pool_results(results, add_sky_temple_key_distribution_logic(db, configuration.sky_temple_keys))


def corruption_specific_pool(results: PoolResults, configuration: CorruptionConfiguration, db: ResourceDatabase):
    # Adding Energy Cells to pool
    _extend_pool_results(results, add_energy_cells(db))


_GAME_SPECIFIC = typing.cast(Dict[RandovaniaGame, Callable[[PoolResults, BaseConfiguration, ResourceDatabase], None]], {
    RandovaniaGame.METROID_PRIME: prime1_specific_pool,
    RandovaniaGame.METROID_PRIME_ECHOES: echoes_specific_pool,
    RandovaniaGame.METROID_PRIME_CORRUPTION: corruption_specific_pool,
})


def calculate_pool_results(layout_configuration: BaseConfiguration,
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

    _GAME_SPECIFIC[layout_configuration.game](base_results, layout_configuration, resource_database)

    return base_results


def calculate_pool_item_count(layout: BaseConfiguration) -> Tuple[int, int]:
    """
    Calculate how many pickups are needed for given layout, with how many spots are there.
    :param layout:
    :return:
    """
    game_description = default_database.game_description_for(layout.game)
    num_pickup_nodes = game_description.world_list.num_pickup_nodes
    pool_pickup = calculate_pool_results(layout, game_description.resource_database).pickups
    min_starting_items = layout.major_items_configuration.minimum_random_starting_items
    maximum_size = num_pickup_nodes + min_starting_items
    return len(pool_pickup), maximum_size
