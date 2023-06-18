from random import Random

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.am2r.layout.am2r_configuration import AM2RConfiguration
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_am2r_artifact
from randovania.generator.pickup_pool.pool_creator import _extend_pool_results
from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDescription,
                 base_patches: GamePatches, rng: Random) -> None:
    assert isinstance(configuration, AM2RConfiguration)

    _extend_pool_results(results, artifact_pool(game, configuration, rng))


def artifact_pool(game: GameDescription, configuration: AM2RConfiguration, rng: Random) -> PoolResults:
    config = configuration.artifacts

    new_assignment: dict[PickupIndex, PickupEntry] = {}

    keys: list[PickupEntry] = [create_am2r_artifact(i, game.resource_database) for i in range(46)]

    keys_to_shuffle = keys[:config.required_artifacts]
    starting_keys = keys[config.required_artifacts:]

    locations: list[NodeIdentifier] = []
    if config.prefer_metroids:
        locations.extend(_METROID_INDICES)
    if config.prefer_bosses:
        locations.extend(_BOSS_INDICES)

    item_pool = keys_to_shuffle

    if rng is not None:
        rng.shuffle(locations)
        new_assignment = {
            game.region_list.get_pickup_node(location).pickup_index: key
            for location, key in zip(locations, keys_to_shuffle)
        }
        item_pool = [key for key in keys_to_shuffle if key not in new_assignment.values()]

    return PoolResults(item_pool, new_assignment, starting_keys)

_c = NodeIdentifier.create
_METROID_INDICES = [
    # Alphas
    _c("Main Caves", "Surface Alpha Nest", "Pickup (Alpha)"),
    _c("Golden Temple", "Exterior Alpha Nest", "Pickup (Alpha)"),
    _c("Golden Temple", "Breeding Grounds North West", "Pickup (Alpha)"),
    _c("Golden Temple", "Breeding Grounds South West", "Pickup (Alpha)"),
    _c("Golden Temple", "Breeding Grounds South East", "Pickup (Alpha)"),
    _c("Hydro Station", "Hydro Station Entrance", "Pickup (Alpha)"),
    _c("Hydro Station", "Exterior Alpha Nest", "Pickup (Alpha)"),
    _c("Hydro Station", "Inner Alpha Nest North", "Pickup (Alpha)"),
    _c("Hydro Station", "Inner Alpha Nest South", "Pickup (Alpha)"),
    _c("Hydro Station", "Breeding Grounds Alpha Nest West", "Pickup (Alpha)"),
    _c("Hydro Station", "Breeding Grounds Alpha Nest East", "Pickup (Alpha)"),
    _c("Hydro Station", "Breeding Grounds Alpha Nest South", "Pickup (Alpha)"),
    _c("Industrial Complex", "Upper Factory Alpha Nest", "Pickup (Alpha)"),
    _c("Industrial Complex", "Breeding Grounds Alpha Nest", "Pickup (Alpha)"),
    _c("Main Caves", "Research Site", "Pickup (Left Alpha)"),
    _c("Main Caves", "Research Site", "Pickup (Right Alpha)"),
    _c("Main Caves", "Mines Alpha Nest", "Pickup (Alpha)"),
    _c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Top Alpha)"),
    _c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Middle Alpha)"),
    _c("Distribution Center", "Alpha Squad Nest", "Pickup (Left Bottom Alpha)"),
    _c("Distribution Center", "Alpha Squad Nest", "Pickup (Right Top Alpha)"),
    _c("Distribution Center", "Alpha Squad Nest", "Pickup (Right Bottom Alpha)"),
    _c("The Nest", "Hideout Alpha Nest", "Pickup (Alpha)"),
    # Gammas
    _c("Hydro Station", "Breeding Grounds Gamma Nest", "Pickup (Gamma)"),
    _c("Industrial Complex", "Exterior Gamma Nest", "Pickup (Gamma)"),
    _c("Industrial Complex", "Upper Factory Gamma Nest", "Pickup (Gamma)"),
    _c("Industrial Complex", "Lower Factory Gamma Nest", "Pickup (Gamma)"),
    _c("Industrial Complex", "Breeding Grounds Gamma Nest West", "Pickup (Gamma)"),
    _c("Industrial Complex", "Breeding Grounds Gamma Nest Bottom", "Pickup (Gamma)"),
    _c("Industrial Complex", "Breeding Grounds Gamma Nest Middle", "Pickup (Gamma)"),
    _c("Industrial Complex", "Breeding Grounds Gamma Nest Top", "Pickup (Gamma)"),
    _c("Industrial Complex", "Breeding Grounds Gamma Nest East", "Pickup (Gamma)"),
    _c("Main Caves", "Mines Gamma Nest", "Pickup (Gamma)"),
    _c("The Tower", "Gamma Nest South East", "Pickup (Gamma)"),
    _c("The Tower", "Gamma Nest North East", "Pickup (Gamma)"),
    _c("The Tower", "Gamma Nest West", "Pickup (Gamma)"),
    _c("Distribution Center", "Dual Gamma Nest", "Pickup (Left Gamma)"),
    _c("Distribution Center", "Dual Gamma Nest", "Pickup (Right Gamma)"),
    # Zetas
    _c("The Tower", "Exterior Zeta Nest East", "Pickup (Zeta)"),
    _c("The Tower", "Exterior Zeta Nest West", "Pickup (Zeta)"),
    _c("The Tower", "Inner Zeta Nest", "Pickup (Zeta)"),
    _c("Distribution Center", "Energy Distribution Zeta Nest", "Pickup (Zeta)"),
    # Omegas
    _c("The Nest", "Hideout Omega Nest", "Pickup (Omega)"),
    _c("The Nest", "Depths Omega Nest East", "Pickup (Omega)"),
    _c("The Nest", "Depths Omega Nest North West", "Pickup (Omega)"),
    _c("The Nest", "Depths Omega Nest South West", "Pickup (Omega)")
]

_BOSS_INDICES = [
    _c("Golden Temple", "Torture Room", "Pickup (Missile Tank)"),
    _c("Hydro Station", "Arachnus Arena", "Pickup (Spring Ball)"),
    _c("Industrial Complex", "Torizo Arena", "Pickup (Space Jump)"),
    _c("The Tower", "Plasma Beam Chamber", "Pickup (Plasma Beam)"),
    _c("Distribution Center", "Ice Beam Chamber", "Pickup (Ice Beam)"),
    _c("GFS Thoth", "Genesis Arena", "Pickup (Energy Tank)")
]

