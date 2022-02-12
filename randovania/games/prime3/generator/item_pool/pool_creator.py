from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime3.generator.item_pool.energy_cells import add_energy_cells
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration


def corruption_specific_pool(results: PoolResults, configuration: BaseConfiguration, db: ResourceDatabase,
                             base_patches: GamePatches, rng: Random):
    assert isinstance(configuration, CorruptionConfiguration)
    # Adding Energy Cells to pool
    _extend_pool_results(results, add_energy_cells(db))
