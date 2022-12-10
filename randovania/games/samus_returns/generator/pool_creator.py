from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
from randovania.generator.item_pool import PoolResults, pickup_creator
from randovania.layout.base.base_configuration import BaseConfiguration

def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, MSRConfiguration)
