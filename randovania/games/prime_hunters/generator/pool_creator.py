from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersArtifactConfig,
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, HuntersConfiguration)

    # Add Alimbic Artifacts to the item pool
    results.extend_with(add_alimbic_artifacts(game, configuration.artifacts))

    # Add Octoliths to the item pool
    results.extend_with(add_octoliths(game, configuration.octoliths))


def add_alimbic_artifacts(
    game: GameDatabaseView,
    config: HuntersArtifactConfig,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    artifacts: list[PickupEntry] = []
    for region in ("Celestial", "Alinos", "Arcterra", "VDO"):
        for i in range(2):
            for artifact_type in ("Cartograph", "Attameter", "Binary Subscripture"):
                artifact = f"{artifact_type} Artifact"
                artifacts.append(
                    create_generated_pickup(
                        artifact, game.get_resource_database_view(), game.get_pickup_database(), i=i + 1, region=region
                    )
                )

    artifacts_per_portal = [
        config.celestial_archives_1,
        config.celestial_archives_2,
        config.alinos_1,
        config.alinos_2,
        config.arcterra_1,
        config.arcterra_2,
        config.vesper_defense_outpost_1,
        config.vesper_defense_outpost_2,
    ]

    artifacts_to_shuffle = []
    start = 0
    for index in range(0, 24, 3):
        difference = index + 3 - artifacts_per_portal[start]
        artifacts_to_shuffle.extend(artifacts[index:difference])
        start += 1

    starting_artifacts = list(set(artifacts) - set(artifacts_to_shuffle))

    return PoolResults(artifacts_to_shuffle, {}, starting_artifacts)


def add_octoliths(
    game: GameDatabaseView,
    config: HuntersOctolithConfig,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    octoliths: list[PickupEntry] = [
        create_generated_pickup("Octolith", game.get_resource_database_view(), game.get_pickup_database(), i=i + 1)
        for i in range(8)
    ]

    octoliths_to_shuffle = octoliths[: config.placed_octoliths]
    starting_octoliths = octoliths[config.placed_octoliths :]

    return PoolResults(octoliths_to_shuffle, {}, starting_octoliths)
