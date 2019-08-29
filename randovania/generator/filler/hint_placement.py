from random import Random
from typing import Callable

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.resolver.state import State

_NUM_REGULAR_HINTS = 22

# TODO: this should be a flag in PickupNode
_SPECIAL_HINTS = {
    PickupIndex(24):  HintType.LIGHT_SUIT_LOCATION,  # Light Suit
    PickupIndex(43):  HintType.GUARDIAN, # Dark Suit (Amorbis)
    PickupIndex(79):  HintType.GUARDIAN, # Dark Visor (Chykka)
    PickupIndex(115): HintType.GUARDIAN, # Annihilator Beam (Quadraxis)
}


def _should_have_hint(item_category: ItemCategory) -> bool:
    return item_category.is_major_category or item_category == ItemCategory.TEMPLE_KEY

def _hint_for_index(index: PickupIndex) -> Hint:
    if index in _SPECIAL_HINTS:
        return Hint(_SPECIAL_HINTS[index], PrecisionPair.detailed(), index)
    else:
        return Hint(HintType.LOCATION, None, index)

def place_hints(final_state: State, rng: Random, world_list: WorldList, status_update: Callable[[str], None]) -> GamePatches:
    status_update("Placing hints...")

    patches = final_state.patches
    special_hints = _SPECIAL_HINTS.copy()

    state_sequence = [final_state]
    while state_sequence[-1].previous_state:
        state_sequence.append(state_sequence[-1].previous_state)
    state_sequence = tuple(reversed(state_sequence))

    indices_with_hints = {index for index, pickup in final_state.patches.pickup_assignment.items()
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

    index_list = sum((indices for indices, _ in sequence), [])
    hints_placed = 0
    for indices, logbooks in sequence:
        while index_list and index_list[0] in indices:
            del index_list[0]
        while index_list and logbooks and hints_placed + len(special_hints) < _NUM_REGULAR_HINTS:
            hint_index = index_list.pop(0)
            if hint_index in special_hints:
                del special_hints[hint_index]

            patches = patches.assign_hint(logbooks.pop(0), _hint_for_index(hint_index))
            hints_placed += 1

    # Place remaining Guardian/vanilla Light Suit hints
    if hints_placed < _NUM_REGULAR_HINTS:
        unassigned_logbook_assets = [node.resource() for node in world_list.all_nodes
                                     if isinstance(node, LogbookNode) and node.resource() not in patches.hints
                                     and node.lore_type.holds_generic_hint]
        rng.shuffle(unassigned_logbook_assets)

        for index, logbook in zip(special_hints, unassigned_logbook_assets):
            patches = patches.assign_hint(logbook, _hint_for_index(index))
            hints_placed += 1

    #print(f"Hints placed: {hints_placed}")

    return patches