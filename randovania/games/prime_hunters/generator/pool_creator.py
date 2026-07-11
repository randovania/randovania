from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, HuntersConfiguration)

    # Add Alimbic Artifacts to the item pool
    results.extend_with(add_alimbic_artifacts(game.get_resource_database_view(), game.get_pickup_database()))

    # Add Octoliths to the item pool
    results.extend_with(add_octoliths(game, configuration.octoliths))

    # Add Shield Keys to the item pool
    results.extend_with(add_shield_keys(game.get_resource_database_view(), game.get_pickup_database()))


def add_alimbic_artifacts(
    resource_database: ResourceDatabaseView,
    pickup_database: PickupDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :param pickup_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for region in ("Celestial", "Alinos", "Arcterra", "VDO"):
        for artifact_type in ("Cartograph", "Attameter", "Binary Subscripture"):
            for i in range(2):
                artifact = f"{artifact_type} Artifact"
                item_pool.append(
                    create_generated_pickup(artifact, resource_database, pickup_database, i=i + 1, region=region)
                )

    return PoolResults(item_pool, {}, [])


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


def add_shield_keys(resource_database: ResourceDatabaseView, pickup_database: PickupDatabase) -> PoolResults:
    """
    :param resource_database:
    :param pickup_database::
    :return:
    """
    item_pool: list[PickupEntry] = []
    shield_key_list: dict[str, list[str]] = {
        "Alinos": [
            "EchoHall",
            "ElderPassage",
            "HighGround",
            "CrashSite",
            "CouncilChamber",
            "PistonCave",
        ],
        "CelestialArchives": [
            "DataShrine01",
            "DataShrine03",
            "SynergyCore",
            "DockingBay",
            "IncubationVault01",
            "NewArrivalRegistration",
        ],
        "VDO": [
            "WeaponsComplexSylux",
            "WeaponsComplexPsychoBits",
            "CompressionChamber",
            "StasisBunkerPuzzle",
            "StasisBunkerGuardians",
            "FuelStack",
        ],
        "Arcterra": [
            "SicTransit",
            "IceHive",
            "FrostLabyrinth",
            "FaultLine",
            "Sanctorus",
            "Subterranean",
        ],
    }

    for region, areas in shield_key_list.items():
        for area in areas:
            item_pool.append(
                create_generated_pickup("Shield Key", resource_database, pickup_database, region=region, area=area)
            )

    return PoolResults(item_pool, {}, [])
