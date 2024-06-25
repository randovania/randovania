from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.blank.layout.blank_configuration import BlankConfiguration
from randovania.games.game import RandovaniaGame

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.generator.pickup_pool import PoolResults
    from randovania.layout.base.base_configuration import BaseConfiguration


def create_victory_key(resource_database: ResourceDatabaseView) -> PickupEntry:
    return PickupEntry(
        name="Victory Key",
        progression=((resource_database.get_item("VictoryKey"), 1),),
        model=PickupModel(game=RandovaniaGame.BLANK, name="VictoryKey"),
        pickup_category=pickup_category.GENERIC_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, BlankConfiguration)

    results.to_place.append(create_victory_key(game.get_resource_database_view()))
