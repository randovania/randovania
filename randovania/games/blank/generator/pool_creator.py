from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.pickup import pickup_category
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel, PickupGeneratorParams
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.base.base_configuration import BaseConfiguration


def create_victory_key(resource_database: ResourceDatabase):
    return PickupEntry(
        name="Victory Key",
        progression=((resource_database.get_item("VictoryKey"), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name="VictoryKey"
        ),
        pickup_category=pickup_category.GENERIC_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, BlankConfiguration)

    results.to_place.append(
        create_victory_key(game.resource_database)
    )
