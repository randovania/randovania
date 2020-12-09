from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.games.game import RandovaniaGame
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.ammo import add_ammo
from randovania.generator.item_pool.dark_temple_keys import add_dark_temple_keys
from randovania.generator.item_pool.energy_cells import add_energy_cells
from randovania.generator.item_pool.artifacts import add_artifacts
from randovania.generator.item_pool.major_items import add_major_items
from randovania.generator.item_pool.sky_temple_keys import add_sky_temple_key_distribution_logic
from randovania.layout.echoes_configuration import EchoesConfiguration


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results.pickups.extend(extension.pickups)
    base_results.assignment.update(extension.assignment)
    add_resources_into_another(base_results.initial_resources, extension.initial_resources)


def calculate_pool_results(layout_configuration: EchoesConfiguration,
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

    if layout_configuration.game == RandovaniaGame.PRIME2:
        # Adding Dark Temple Keys to pool
        _extend_pool_results(base_results, add_dark_temple_keys(resource_database))

        # Adding Sky Temple Keys to pool
        _extend_pool_results(base_results,
                             add_sky_temple_key_distribution_logic(resource_database,
                                                                   layout_configuration.sky_temple_keys))

    elif layout_configuration.game == RandovaniaGame.PRIME3:
        # Adding Energy Cells to pool
        _extend_pool_results(base_results, add_energy_cells(resource_database))

    elif layout_configuration.game == RandovaniaGame.PRIME1:
        _extend_pool_results(base_results, add_artifacts(resource_database))

    return base_results
