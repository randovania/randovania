from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import (
    PlanetsZebethArtifactConfig,
    PlanetsZebethConfiguration,
)
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration

TOURIAN_KEY_CATEGORY = pickup_category.PickupCategory(
    name="key", long_name="Tourian Key", hint_details=("some ", "key"), hinted_as_major=False, is_key=True
)


def create_planets_zebeth_artifact(
    artifact_number: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    return PickupEntry(
        name=f"Tourian Key {artifact_number + 1}",
        progression=((resource_database.get_item("Tourian Key"), 1),),
        model=PickupModel(game=resource_database.game_enum, name="spr_ITEM_Tourian_Key"),
        pickup_category=TOURIAN_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, PlanetsZebethConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: PlanetsZebethArtifactConfig) -> PoolResults:
    keys: list[PickupEntry] = [create_planets_zebeth_artifact(i, game.resource_database) for i in range(9)]

    # Check if we have vanilla tourian keys checked
    if config.vanilla_tourian_keys:
        return PoolResults([], {PickupIndex(38): keys[0], PickupIndex(40): keys[1]}, keys[2:])

    # Check whether we have valid artifact requirements in configuration
    if config.required_artifacts > 9:
        raise InvalidConfiguration("More Tourian Keys than allowed!")

    keys_to_shuffle = keys[: config.required_artifacts]
    starting_keys = keys[config.required_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
