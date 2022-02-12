from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.layout.base.base_configuration import BaseConfiguration


def super_metroid_specific_pool(results: PoolResults, configuration: BaseConfiguration, db: ResourceDatabase,
                                base_patches: GamePatches, rng: Random):
    assert isinstance(configuration, SuperMetroidConfiguration)
    pass
