from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig, DreadConfiguration
from randovania.games.game import RandovaniaGame
from randovania.generator.pickup_pool import PoolResults

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.layout.base.base_configuration import BaseConfiguration

DREAD_ARTIFACT_CATEGORY = pickup_category.PickupCategory(
    name="dna", long_name="Metroid DNA", hint_details=("some ", "Metroid DNA"), hinted_as_major=False, is_key=True
)


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription) -> None:
    assert isinstance(configuration, DreadConfiguration)

    results.extend_with(artifact_pool(game, configuration.artifacts))


def artifact_pool(game: GameDescription, config: DreadArtifactConfig) -> PoolResults:
    keys = [create_dread_artifact(i, game.resource_database) for i in range(12)]
    keys_to_shuffle = keys[: config.required_artifacts]
    starting_keys = keys[config.required_artifacts :]

    return PoolResults(keys_to_shuffle, {}, starting_keys)


def create_dread_artifact(
    artifact_number: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    return PickupEntry(
        name=f"Metroid DNA {artifact_number + 1}",
        progression=((resource_database.get_item(f"Artifact{artifact_number + 1}"), 1),),
        model=PickupModel(game=resource_database.game_enum, name=f"DNA_{artifact_number + 1}"),
        pickup_category=DREAD_ARTIFACT_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict({RandovaniaGame.AM2R: "sItemDNA"}),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
        ),
    )
