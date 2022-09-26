from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.generator.item_pool import PoolResults, pickup_creator
from randovania.layout.base.base_configuration import BaseConfiguration


def create_victory_key(resource_database: ResourceDatabase):
    return PickupEntry(
        name="Victory Key",
        progression=((resource_database.get_item("VictoryKey"), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name="VictoryKey"
        ),
        item_category=pickup_creator.GENERIC_KEY_CATEGORY,
        broad_category=pickup_creator.GENERIC_KEY_CATEGORY,
        probability_offset=0.25,
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, BlankConfiguration)

    results.pickups.append(
        create_victory_key(game.resource_database)
    )
