from random import Random
from typing import List, Tuple, Callable

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.generator.filler.retcon import retcon_playthrough_filler
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver import bootstrap
from randovania.resolver.state import State


def _split_expansions(item_pool: List[PickupEntry]) -> Tuple[List[PickupEntry], List[PickupEntry]]:
    """

    :param item_pool:
    :return:
    """
    major_items = []
    expansions = []

    for pickup in item_pool:
        if pickup.item_category == ItemCategory.EXPANSION:
            expansions.append(pickup)
        else:
            major_items.append(pickup)

    return major_items, expansions


def run_filler(configuration: LayoutConfiguration,
               game: GameDescription,
               item_pool: List[PickupEntry],
               patches: GamePatches,
               rng: Random,
               status_update: Callable[[str], None],
               ) -> Tuple[State, List[PickupEntry]]:
    """
    Runs the filler logic for the given configuration and item pool.
    Returns a GamePatches with progression items assigned, along with all items in the pool
    that weren't assigned.

    :param configuration:
    :param game:
    :param item_pool:
    :param patches:
    :param rng:
    :param status_update:
    :return:
    """
    major_items, expansions = _split_expansions(item_pool)
    rng.shuffle(major_items)
    rng.shuffle(expansions)

    major_configuration = configuration.major_items_configuration

    new_game, state = bootstrap.logic_bootstrap(configuration, game, patches)
    new_game.simplify_connections(state.resources)

    final_state = retcon_playthrough_filler(
        new_game, state, major_items, rng,
        randomization_mode=configuration.randomization_mode,
        minimum_random_starting_items=major_configuration.minimum_random_starting_items,
        maximum_random_starting_items=major_configuration.maximum_random_starting_items,
        status_update=status_update)

    return final_state, major_items + expansions
