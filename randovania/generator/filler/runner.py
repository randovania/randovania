import copy
import dataclasses
from random import Random
from typing import List, Tuple, Callable, TypeVar

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world_list import WorldList
from randovania.generator.filler.retcon import retcon_playthrough_filler
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver import bootstrap

T = TypeVar("T")


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


def _create_weighted_list(rng: Random,
                          current: List[T],
                          factory: Callable[[], List[T]],
                          ) -> List[T]:
    """
    Ensures we always have a non-empty list.
    :param rng:
    :param current:
    :param factory:
    :return:
    """
    if not current:
        current = factory()
        rng.shuffle(current)

    return current


def add_hints_precision(patches: GamePatches,
                        rng: Random,
                        ) -> GamePatches:
    """
    Adds precision to all hints that are missing one.
    :param patches:
    :param rng:
    :return:
    """

    hints_to_replace = {
        asset: hint
        for asset, hint in patches.hints.items()
        if hint.precision is None
    }

    asset_ids = list(hints_to_replace.keys())

    # Add random precisions
    rng.shuffle(asset_ids)
    precisions = []
    for asset_id in asset_ids:
        precisions = _create_weighted_list(rng, precisions, PrecisionPair.weighted_list)
        precision = precisions.pop()

        hints_to_replace[asset_id] = dataclasses.replace(hints_to_replace[asset_id], precision=precision)

    # Replace the hints the in the patches
    return dataclasses.replace(patches, hints={
        asset: hints_to_replace.get(asset, hint)
        for asset, hint in patches.hints.items()
    })


def replace_hints_without_precision_with_jokes(patches: GamePatches,
                                               ) -> GamePatches:
    """
    Adds WRONG_GAME precision to all hints that are missing one precision.
    :param patches:
    :return:
    """

    hints_to_replace = {
        asset: dataclasses.replace(hint, precision=PrecisionPair.joke())
        for asset, hint in patches.hints.items()
        if hint.precision
    }

    return dataclasses.replace(patches, hints={
        asset: hints_to_replace.get(asset, hint)
        for asset, hint in patches.hints.items()
    })


def fill_unassigned_hints(patches: GamePatches,
                          world_list: WorldList,
                          rng: Random,
                          ) -> GamePatches:

    new_hints = copy.copy(patches.hints)
    possible_indices = list(patches.pickup_assignment.keys())

    for node in world_list.all_nodes:
        if isinstance(node, LogbookNode):
            logbook_asset = node.resource()
            if logbook_asset not in new_hints:
                new_hints[logbook_asset] = Hint(HintType.LOCATION, None, rng.choice(possible_indices))

    return dataclasses.replace(patches, hints=new_hints)


def run_filler(configuration: LayoutConfiguration,
               game: GameDescription,
               item_pool: List[PickupEntry],
               patches: GamePatches,
               rng: Random,
               status_update: Callable[[str], None],
               ) -> Tuple[GamePatches, List[PickupEntry]]:
    """
    Runs the filler logic for the given configuration and item pool.
    Returns a GamePatches with progression items and hints assigned, along with all items in the pool
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

    filler_patches = retcon_playthrough_filler(
        new_game, state, major_items, rng,
        minimum_random_starting_items=major_configuration.minimum_random_starting_items,
        maximum_random_starting_items=major_configuration.maximum_random_starting_items,
        status_update=status_update)

    # Since we haven't added expansions yet, these hints will always be for items added by the filler.
    full_hints_patches = fill_unassigned_hints(filler_patches, game.world_list, rng)

    if configuration.hints.item_hints:
        result = add_hints_precision(full_hints_patches, rng)
    else:
        result = replace_hints_without_precision_with_jokes(full_hints_patches)

    return result, major_items + expansions
