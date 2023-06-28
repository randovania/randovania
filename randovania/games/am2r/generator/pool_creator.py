from random import Random

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_am2r_artifact
from randovania.generator.pickup_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.exceptions import InvalidConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, AM2RConfiguration)

    _extend_pool_results(results, artifact_pool(game, configuration, rng))


def artifact_pool(game: GameDescription, configuration: AM2RConfiguration, rng: Random) -> PoolResults:
    config = configuration.artifacts

    # Check whether we have valid artifact requirements in configuration
    max_artifacts = 0
    if config.prefer_metroids:
        max_artifacts = 46
    elif config.prefer_bosses:
        max_artifacts = 6
    if config.required_artifacts > max_artifacts:
        raise InvalidConfiguration("More Metroid DNA than allowed!")

    new_assignment: dict[PickupIndex, PickupEntry] = {}

    keys: list[PickupEntry] = [create_am2r_artifact(i, game.resource_database) for i in range(46)]

    keys_to_shuffle = keys[:config.required_artifacts]
    starting_keys = keys[config.required_artifacts:]

    locations: list[PickupNode] = []
    for node in game.region_list.all_nodes:
        if isinstance(node, PickupNode):
            # Metroid pickups
            name = node.extra["object_name"]
            if config.prefer_metroids and name.startswith("oItemDNA_"):
                locations.append(node)
            # Pickups guarded by bosses
            elif config.prefer_bosses and name in _boss_items:
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


_boss_items = [
    "oItemM_111",
    "oItemJumpBall",
    "oItemSpaceJump",
    "oItemPBeam",
    "oItemIBeam",
    "oItemETank_50"
]