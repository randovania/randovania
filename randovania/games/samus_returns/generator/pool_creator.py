from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.base.base_configuration import BaseConfiguration

def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, MSRConfiguration)
