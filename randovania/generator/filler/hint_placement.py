import dataclasses
from random import Random
from typing import Callable, List, TypeVar, Union

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
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

    state_sequence = [final_state]
    while state_sequence[-1].previous_state:
        state_sequence.append(state_sequence[-1].previous_state)
    state_sequence = tuple(reversed(state_sequence))

    possible_hint_indices = {index for index, pickup in patches.pickup_assignment.items()
                             if pickup.can_get_hint or index in _SPECIAL_HINTS}

    sequence: List[Union[PickupIndex, LogbookAsset]] = []
    for state in state_sequence[1:]:
        new_indices = sorted((set(state.collected_pickup_indices) & possible_hint_indices)
                             - set(state.previous_state.collected_pickup_indices))
        rng.shuffle(new_indices)

        new_logbook_assets = sorted(set(state.collected_scan_assets)
                                  - (set(state.previous_state.collected_scan_assets) | set(patches.hints)))
        rng.shuffle(new_logbook_assets)

        sequence.extend((*new_indices, *new_logbook_assets))

    sequence_types = [type(resource) for resource in sequence]
    indices_with_hints = set()
    special_hint_indices_remaining = set(_SPECIAL_HINTS)

    unassigned_logbook_assets = [node.resource() for node in world_list.all_nodes
                                 if isinstance(node, LogbookNode) and node.lore_type.holds_generic_hint
                                 and node.resource() not in patches.hints]
    rng.shuffle(unassigned_logbook_assets)

    # Fill hint locations with hints for in-sequence items
    for i, resource in enumerate(sequence):
        if isinstance(resource, LogbookAsset) and len(unassigned_logbook_assets) > len(special_hint_indices_remaining):
            hint_logbook = resource

            # Forbid hints for the index such that there are not other indices between it and our current logbook
            # asset in the sequence. This prevents hints for items in the same room as the hints if the item is
            # collectable at the same time as the hint (which is usually the case).
            for resource in sequence[sequence_types.index(PickupIndex, i) + 1:]:
                if isinstance(resource, PickupIndex) and resource not in indices_with_hints:
                    hint_index = resource
                    break
            else:
                break

            patches = patches.assign_hint(hint_logbook, _hint_for_index(hint_index))
            indices_with_hints.add(hint_index)
            special_hint_indices_remaining.discard(hint_index)
            unassigned_logbook_assets.remove(hint_logbook)

    # Place remaining Guardian/vanilla Light Suit hints
    for index in special_hint_indices_remaining:
        patches = patches.assign_hint(unassigned_logbook_assets.pop(), _hint_for_index(index))

    # Try to fill remaining hint locations with hints for indices that come after all of the logbook assets
    # in the sequence
    if unassigned_logbook_assets:
        end_of_sequence_indices = []
        for resource in reversed(sequence):
            if isinstance(resource, LogbookAsset):
                break
            elif resource not in indices_with_hints:
                end_of_sequence_indices.append(resource)
        rng.shuffle(end_of_sequence_indices)

        while unassigned_logbook_assets and end_of_sequence_indices:
            hint_index = end_of_sequence_indices.pop()
            hint_logbook = unassigned_logbook_assets.pop()
            patches = patches.assign_hint(hint_logbook, _hint_for_index(hint_index))
            indices_with_hints.add(hint_index)

    # Try to fill remaining hint locations with hints for indices that aren't in the sequence
    if unassigned_logbook_assets:
        out_of_sequence_indices = list(possible_hint_indices - indices_with_hints - set(sequence))
        rng.shuffle(out_of_sequence_indices)

        while unassigned_logbook_assets and out_of_sequence_indices:
            hint_index = out_of_sequence_indices.pop()
            hint_logbook = unassigned_logbook_assets.pop()
            patches = patches.assign_hint(hint_logbook, _hint_for_index(hint_index))
            indices_with_hints.add(hint_index)

    # Fill remaining hint locations with jokes
    while unassigned_logbook_assets:
        patches = patches.assign_hint(unassigned_logbook_assets.pop(),
                                      Hint(HintType.LOCATION, PrecisionPair.joke(), PickupIndex(-1))
                                      )

    # Fill in hint precisions
    if configuration.hints.item_hints:
        patches = add_hint_precisions(patches, rng)
    else:
        patches = replace_hints_without_precision_with_jokes(patches)

    return patches