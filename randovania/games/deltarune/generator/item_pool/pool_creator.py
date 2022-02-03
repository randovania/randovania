from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.deltarune.generator.item_pool.artifacts import add_keyitem
from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pool_creator import _extend_pool_results


def deltarune_specific_pool(results: PoolResults, configuration: deltaruneConfiguration, db: ResourceDatabase,
                         patches: GamePatches, rng: Random):
    _extend_pool_results(results, add_keyitem(db, configuration.keyitem_target,
                                                configuration.keyitem_minimum_progression))
