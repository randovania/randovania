from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.patcher import prime_items
from randovania.generator.pickup_pool import PoolResults

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode

ARTIFACT_CATEGORY = pickup_category.PickupCategory(
    name="artifact", long_name="Artifact", hint_details=("an ", "artifact"), hinted_as_major=False, is_key=True
)


def add_artifacts(
    resource_database: ResourceDatabase,
    total: LayoutArtifactMode,
    artifact_minimum_progression: int,
) -> PoolResults:
    """
    :param resource_database:
    :param total
    :param artifact_minimum_progression
    :return:
    """
    item_pool: list[PickupEntry] = []

    artifacts_to_place = total.value

    for i in range(artifacts_to_place):
        item_pool.append(create_artifact(i, artifact_minimum_progression, resource_database))

    first_automatic_artifact = artifacts_to_place

    starting = [
        create_artifact(automatic_artifact, artifact_minimum_progression, resource_database)
        for automatic_artifact in range(first_automatic_artifact, 12)
    ]

    return PoolResults(item_pool, {}, starting)


def create_artifact(
    artifact_index: int,
    minimum_progression: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    return PickupEntry(
        name=prime_items.ARTIFACT_NAMES[artifact_index],
        progression=((resource_database.get_item(prime_items.ARTIFACT_ITEMS[artifact_index]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=prime_items.ARTIFACT_MODEL[artifact_index],
        ),
        pickup_category=ARTIFACT_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict(
            {RandovaniaGame.AM2R: f"sItemArtifact{prime_items.ARTIFACT_ITEMS[artifact_index]}Prime"}
        ),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=0.25,
            required_progression=minimum_progression,
        ),
    )
