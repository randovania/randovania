from randovania.games.prime3.generator.item_pool.energy_cells import add_energy_cells
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.generator.item_pool import PoolResults
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.generator.item_pool.pool_creator import _extend_pool_results


def corruption_specific_pool(results: PoolResults, configuration: CorruptionConfiguration, db: ResourceDatabase):
    # Adding Energy Cells to pool
    _extend_pool_results(results, add_energy_cells(db))
