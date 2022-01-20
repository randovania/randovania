from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime1.generator.item_pool.artifacts import add_artifacts
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pool_creator import _extend_pool_results


def prime1_specific_pool(results: PoolResults, configuration: PrimeConfiguration, db: ResourceDatabase,
                         patches: GamePatches, rng: Random):
    _extend_pool_results(results, add_artifacts(db, configuration.artifact_target,
                                                configuration.artifact_minimum_progression))
