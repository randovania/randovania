from random import Random

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pickup_creator import create_dread_artifact
from randovania.generator.item_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, db: ResourceDatabase,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, DreadConfiguration)

    _extend_pool_results(results, artifact_pool(db, configuration, rng))


def artifact_pool(resource_database: ResourceDatabase, configuration: DreadConfiguration, rng: Random) -> PoolResults:
    config = configuration.artifacts

    new_assignment: dict[PickupIndex, PickupEntry] = {}
    initial_resources = ResourceCollection.with_database(resource_database)

    keys: list[PickupEntry] = [create_dread_artifact(i, resource_database) for i in range(12)]

    keys_to_shuffle = keys[:config.required_artifacts]
    starting_keys = keys[config.required_artifacts:]

    for key in starting_keys:
        initial_resources.add_resource_gain(key.progression)

    locations: list[PickupIndex] = []
    if config.prefer_emmi:
        locations.extend(_EMMI_INDICES)
    if config.prefer_major_bosses:
        locations.extend(_BOSS_INDICES)

    item_pool = keys_to_shuffle

    if rng is not None:
        rng.shuffle(locations)
        new_assignment = {location: key for location, key in zip(locations, keys_to_shuffle)}
        item_pool = [key for key in keys_to_shuffle if key not in new_assignment.values()]

    return PoolResults(item_pool, new_assignment, initial_resources)


_EMMI_INDICES = [
    PickupIndex(139),  # Artaria
    PickupIndex(144),  # Cataris
    PickupIndex(147),  # Dairon
    PickupIndex(143),  # Ferenia
    PickupIndex(146),  # Ghavoran
    PickupIndex(137),  # Hanubia
]

_BOSS_INDICES = [
    PickupIndex(138),  # Corpius
    PickupIndex(142),  # Escue
    PickupIndex(145),  # Golzuna
    PickupIndex(150),  # Drogyga
    PickupIndex(149),  # Experiment Z-57
    PickupIndex(148),  # Kraid
]
