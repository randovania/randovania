from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.games.super_metroid.layout.super_metroid_configuration import SuperMetroidConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.layout.base.base_configuration import BaseConfiguration


def super_metroid_specific_pool(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                                base_patches: GamePatches, rng: Random):
    assert isinstance(configuration, SuperMetroidConfiguration)
    pass
