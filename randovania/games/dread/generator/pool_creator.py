from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.item_pool import PoolResults
from randovania.generator.item_pool.pickup_creator import create_dread_artifact
from randovania.generator.item_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, DreadConfiguration)

    _extend_pool_results(results, artifact_pool(game, configuration, rng))


def artifact_pool(game: GameDescription, configuration: DreadConfiguration, rng: Random) -> PoolResults:
    config = configuration.artifacts

    new_assignment: dict[PickupIndex, PickupEntry] = {}
    initial_resources = ResourceCollection.with_database(game.resource_database)

    keys: list[PickupEntry] = [create_dread_artifact(i, game.resource_database) for i in range(12)]

    keys_to_shuffle = keys[:config.required_artifacts]
    starting_keys = keys[config.required_artifacts:]

    for key in starting_keys:
        initial_resources.add_resource_gain(key.progression)

    locations: list[NodeIdentifier] = []
    if config.prefer_emmi:
        locations.extend(_EMMI_INDICES)
    if config.prefer_major_bosses:
        locations.extend(_BOSS_INDICES)

    item_pool = keys_to_shuffle

    if rng is not None:
        rng.shuffle(locations)
        new_assignment = {
            game.world_list.get_pickup_node(location).pickup_index: key
            for location, key in zip(locations, keys_to_shuffle)
        }
        item_pool = [key for key in keys_to_shuffle if key not in new_assignment.values()]

    return PoolResults(item_pool, new_assignment, initial_resources)


_c = NodeIdentifier.create
_EMMI_INDICES = [
    _c("Artaria", "Central Unit Access", "Pickup (Spider Magnet)"),
    _c("Cataris", "Central Unit Access", "Pickup (Morph Ball)"),
    _c("Dairon", "Central Unit Access", "Pickup (Speed Booster)"),
    _c("Ferenia", "Purple EMMI Arena", "Pickup (Wave Beam)"),
    _c("Ghavoran", "Central Unit Access", "Pickup (Ice Missile)"),
    _c("Hanubia", "Orange EMMI Introduction", "Pickup (Power Bomb)"),
]

_BOSS_INDICES = [
    _c("Artaria", "Corpius Arena", "Pickup (Phantom Cloak)"),
    _c("Ferenia", "Escue Arena", "Pickup (Storm Missile)"),
    _c("Ghavoran", "Golzuna Arena", "Pickup (Cross Bomb)"),
    _c("Burenia", "Drogyga Arena", "Pickup (Drogyga)"),
    _c("Cataris", "Above Z-57 Fight", "Pickup (Z-57)"),
    _c("Cataris", "Kraid Arena", "Pickup (Kraid)"),
]
