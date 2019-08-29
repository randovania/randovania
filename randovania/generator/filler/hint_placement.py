import dataclasses
from random import Random
from typing import Callable, List, TypeVar

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.resolver.state import State

# TODO: this should be a flag in PickupNode
_SPECIAL_HINTS = {
    PickupIndex(24):  HintType.LIGHT_SUIT_LOCATION,  # Light Suit
    PickupIndex(43):  HintType.GUARDIAN, # Dark Suit (Amorbis)
    PickupIndex(79):  HintType.GUARDIAN, # Dark Visor (Chykka)
    PickupIndex(115): HintType.GUARDIAN, # Annihilator Beam (Quadraxis)
}

T = TypeVar("T")

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


def _should_have_hint(item_category: ItemCategory) -> bool:
    return item_category.is_major_category or item_category == ItemCategory.TEMPLE_KEY


def _hint_for_index(index: PickupIndex) -> Hint:
    if index in _SPECIAL_HINTS:
        return Hint(_SPECIAL_HINTS[index], PrecisionPair.detailed(), index)
    else:
        return Hint(HintType.LOCATION, None, index)


def add_hint_precisions(patches: GamePatches, rng: Random) -> GamePatches:
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


def replace_hints_without_precision_with_jokes(patches: GamePatches) -> GamePatches:
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


def place_hints(configuration: LayoutConfiguration, final_state: State, patches: GamePatches, rng: Random,
                world_list: WorldList, status_update: Callable[[str], None]) -> GamePatches:
    status_update("Placing hints...")

    special_hints = _SPECIAL_HINTS.copy()

    state_sequence = [final_state]
    while state_sequence[-1].previous_state:
        state_sequence.append(state_sequence[-1].previous_state)
    state_sequence = tuple(reversed(state_sequence))

    indices_with_hints = {index for index, pickup in patches.pickup_assignment.items()
                          if _should_have_hint(pickup.item_category) or index in special_hints}

    sequence = []
    for state in state_sequence[1:]:
        new_indices = sorted((set(state.collected_pickup_indices) & indices_with_hints)
                           - set(state.previous_state.collected_pickup_indices))
        rng.shuffle(new_indices)

        new_logbook_assets = sorted(set(state.collected_scan_assets)
                                  - (set(state.previous_state.collected_scan_assets) | set(patches.hints)))
        rng.shuffle(new_logbook_assets)

        if sequence and not new_logbook_assets:
            sequence[-1][0].extend(new_indices)
        else:
            sequence.append((new_indices, new_logbook_assets))

        if len(sequence) >= 2:
            sequence[-2][0].extend(new_indices)

    unassigned_logbook_assets = [node.resource() for node in world_list.all_nodes
                                 if isinstance(node, LogbookNode) and node.lore_type.holds_generic_hint]
    rng.shuffle(unassigned_logbook_assets)

    index_list = sum((indices for indices, _ in sequence), [])
    for indices, logbooks in sequence:
        while index_list and index_list[0] in indices:
            del index_list[0]
        while index_list and logbooks and len(unassigned_logbook_assets) > len(special_hints):
            hint_index = index_list.pop(0)
            if hint_index in special_hints:
                del special_hints[hint_index]

            hint_logbook = logbooks.pop(0)
            unassigned_logbook_assets.remove(hint_logbook)

            patches = patches.assign_hint(hint_logbook, _hint_for_index(hint_index))

    # Place remaining Guardian/vanilla Light Suit hints
    for index in special_hints:
        patches = patches.assign_hint(unassigned_logbook_assets.pop(), _hint_for_index(index))

    # Fill remaining hint locations with jokes
    while unassigned_logbook_assets:
        patches = patches.assign_hint(unassigned_logbook_assets.pop(), Hint(HintType.LOCATION, PrecisionPair.joke(), PickupIndex(-1)))

    # Fill in hint precisions
    if configuration.hints.item_hints:
        patches = add_hint_precisions(patches, rng)
    else:
        patches = replace_hints_without_precision_with_jokes(patches)

    return patches