from random import Random

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_dread_artifact
from randovania.generator.pickup_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, DreadConfiguration)

    _extend_pool_results(results, artifact_pool(game, configuration, rng))


def artifact_pool(game: GameDescription, configuration: DreadConfiguration, rng: Random) -> PoolResults:
    config = configuration.artifacts

    new_assignment: dict[PickupIndex, PickupEntry] = {}

    keys: list[PickupEntry] = [create_dread_artifact(i, game.resource_database) for i in range(12)]

    keys_to_shuffle = keys[:config.required_artifacts]
    starting_keys = keys[config.required_artifacts:]

    locations: list[PickupNode] = []
    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode) and "boss_hint_name" in node.extra:
            if node.extra["pickup_type"] == "emmi":
                if config.prefer_emmi:
                    locations.append(node)
            else:
                if config.prefer_major_bosses:
                    locations.append(node)

    item_pool = keys_to_shuffle

    if rng is not None:
        rng.shuffle(locations)
        new_assignment = {
            location.pickup_index: key
            for location, key in zip(locations, keys_to_shuffle)
        }
        item_pool = [key for key in keys_to_shuffle if key not in new_assignment.values()]

    return PoolResults(item_pool, new_assignment, starting_keys)
