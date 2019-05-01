import dataclasses
from random import Random
from typing import List, Tuple, Callable, TypeVar

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintItemPrecision, HintLocationPrecision
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry
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
        if hint.location_precision is None or hint.item_precision is None
    }

    asset_ids = list(hints_to_replace.keys())

    # Add random item precisions
    rng.shuffle(asset_ids)
    item_precisions = []
    for asset_id in asset_ids:
        item_precisions = _create_weighted_list(rng, item_precisions,
                                                HintItemPrecision.weighted_list)
        precision = item_precisions.pop()

        hints_to_replace[asset_id] = dataclasses.replace(hints_to_replace[asset_id], item_precision=precision)

    # Add random location precisions
    rng.shuffle(asset_ids)
    location_precisions = []
    for asset_id in asset_ids:
        location_precisions = _create_weighted_list(rng, location_precisions,
                                                    HintLocationPrecision.weighted_list)
        precision = location_precisions.pop()

        hints_to_replace[asset_id] = dataclasses.replace(hints_to_replace[asset_id], location_precision=precision)

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
        asset: dataclasses.replace(hint,
                                   item_precision=HintItemPrecision.WRONG_GAME,
                                   location_precision=HintLocationPrecision.WRONG_GAME)
        for asset, hint in patches.hints.items()
        if hint.location_precision is None or hint.item_precision is None
    }

    return dataclasses.replace(patches, hints={
        asset: hints_to_replace.get(asset, hint)
        for asset, hint in patches.hints.items()
    })


def run_filler(configuration: LayoutConfiguration,
               game: GameDescription,
               item_pool: List[PickupEntry],
               patches: GamePatches,
               rng: Random,
               status_update: Callable[[str], None],
               ):
    """

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

    logic, state = bootstrap.logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    filler_patches = retcon_playthrough_filler(
        logic, state, major_items, rng,
        minimum_random_starting_items=major_configuration.minimum_random_starting_items,
        maximum_random_starting_items=major_configuration.maximum_random_starting_items,
        status_update=status_update)

    if configuration.hints.item_hints:
        result = add_hints_precision(filler_patches, rng)
    else:
        result = replace_hints_without_precision_with_jokes(filler_patches)

    return result, major_items + expansions
