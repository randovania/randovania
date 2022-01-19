from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.item_pool import PoolResults


def pool_creator(results: PoolResults, configuration: DreadConfiguration, db: ResourceDatabase,
                 base_patches: GamePatches, rng: Random) -> None:
    pass
