from typing import Tuple, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import PickupEntry
from randovania.layout.permalink import Permalink
from randovania.resolver.item_pool import PoolResults
from randovania.resolver.item_pool.sky_temple_keys import add_sky_temple_key_distribution_logic
from randovania.resolver.item_pool.dark_temple_keys import add_dark_temple_keys
from randovania.resolver.item_pool.major_items import add_major_items, _add_energy_tanks
from randovania.resolver.item_pool.ammo import add_ammo


def _extend_pool_results(base_results: PoolResults, extension: PoolResults):
    base_results[0].extend(extension[0])
    base_results[1].update(extension[1])
    base_results[2].extend(extension[2])


def calculate_item_pool(permalink: Permalink,
                        game: GameDescription,
                        patches: GamePatches,
                        ) -> Tuple[GamePatches, List[PickupEntry]]:
    """
    Creates a GamePatches with all starting items and pickups in fixed locations, as well as a list of
    pickups we should shuffle.
    :param permalink:
    :param game:
    :param patches:
    :return:
    """

    layout_configuration = permalink.layout_configuration
    base_results = ([], {}, [])

    # Adding major items to the pool
    new_results, included_ammo_for_item = add_major_items(game, layout_configuration.major_items_configuration)
    _extend_pool_results(base_results, new_results)

    # Adding ammo to the pool
    base_results[0].extend(add_ammo(game, layout_configuration.ammo_configuration, included_ammo_for_item))

    # Adding E-Tanks
    _extend_pool_results(base_results, _add_energy_tanks(game))

    # Adding Dark Temple Keys to pool
    _extend_pool_results(base_results, add_dark_temple_keys(game))

    # Adding Sky Temple Keys to pool
    _extend_pool_results(base_results,
                         add_sky_temple_key_distribution_logic(game, layout_configuration.sky_temple_keys))

    new_patches = patches.assign_pickup_assignment(base_results[1]).assign_extra_initial_items(base_results[2])
    return new_patches, base_results[0]
