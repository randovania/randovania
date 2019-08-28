from random import Random
from typing import Callable

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.resolver.state import State


def _should_have_hint(item_category: ItemCategory) -> bool:
    return item_category.is_major_category or item_category == ItemCategory.TEMPLE_KEY

def place_hints(final_state: State, rng: Random, status_update: Callable[[str], None]) -> GamePatches:
    status_update("Placing hints...")

    patches = final_state.patches

    state_sequence = [final_state]
    while state_sequence[-1].previous_state:
        state_sequence.append(state_sequence[-1].previous_state)
    state_sequence = tuple(reversed(state_sequence))

    indices_with_hints = {index for index, pickup in final_state.patches.pickup_assignment.items()
                          if _should_have_hint(pickup.item_category)}

    sequence = []
    for state in state_sequence[1:]:
        new_indices = list((set(state.collected_pickup_indices) & indices_with_hints)
                           - set(state.previous_state.collected_pickup_indices))
        rng.shuffle(new_indices)

        new_logbook_assets = list(set(state.collected_scan_assets)
                                  - (set(state.previous_state.collected_scan_assets) | set(patches.hints)))
        rng.shuffle(new_logbook_assets)

        if sequence and not new_logbook_assets:
            sequence[-1][0].extend(new_indices)
        else:
            sequence.append((new_indices, new_logbook_assets))

    index_list = sum((indices for indices, _ in sequence), [])
    for indices, logbooks in sequence:
        while index_list and index_list[0] in indices:
            del index_list[0]
        while index_list and logbooks:
            patches = patches.assign_hint(logbooks.pop(0), Hint(HintType.LOCATION, None, index_list.pop(0)))

    return patches