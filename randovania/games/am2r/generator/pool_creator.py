from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig, AM2RConfiguration
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration

METROID_DNA_CATEGORY = pickup_category.PickupCategory(
    name="dna", long_name="Metroid DNA", hint_details=("some ", "Metroid DNA"), hinted_as_major=False, is_key=True
)


def create_am2r_artifact(
    artifact_number: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    return PickupEntry(
        name=f"Metroid DNA {artifact_number + 1}",
        progression=((resource_database.get_item(f"Metroid DNA {artifact_number + 1}"), 1),),
        model=PickupModel(game=resource_database.game_enum, name="sItemDNA"),
        pickup_category=METROID_DNA_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict({RandovaniaGame.METROID_SAMUS_RETURNS: "adn"}),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, AM2RConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: AM2RArtifactConfig) -> PoolResults:
    # Check whether we have valid artifact requirements in configuration
    max_artifacts = 0
    if config.prefer_anywhere:
        max_artifacts = 46
    elif config.prefer_metroids:
        max_artifacts = 46
    elif config.prefer_bosses:
        max_artifacts = 6
    if config.required_artifacts > max_artifacts:
        raise InvalidConfiguration("More Metroid DNA than allowed!")

    keys: list[PickupEntry] = [create_am2r_artifact(i, game.resource_database) for i in range(46)]
    keys_to_shuffle = keys[: config.placed_artifacts]
    starting_keys = keys[config.placed_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)
