from random import Random
from typing import Tuple, List

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.games.prime.patcher_file_lib.hint_name_creator import HintNameCreator, create_simple_logbook_hint

_LORE_SCANS = {
    0x987884FB: "Luminoth Lore translated. (Age of Anxiety)",  # Meeting Grounds
    0x3E0F8F4F: "Luminoth Lore translated. (Agon Falls)",  # Sanctuary Energy Controller
    0x5324575E: "Luminoth Lore translated. (Cataclysm)",  # E3BEF27F

    0xD25C0D22: "Luminoth Lore translated. (Dark Aether)",  # 133BF5B8
    0x692E362E: "Luminoth Lore translated. (Light of Aether)",  # 2BCD44A7
    0x49CD4F34: "Luminoth Lore translated. (New Weapons)",  # 3501473A
    0xC3576EA5: "Luminoth Lore translated. (Origins)",  # 02A01334
    0x39E3A79D: "Luminoth Lore translated. (Our Heritage)",  # 62FF94EE
    0x54C87F8C: "Luminoth Lore translated. (Our War Begins)",  # 80E67F90
    0x24E69725: "Luminoth Lore translated. (Paradise)",  # 427FAD9A
    0x9F94AC29: "Luminoth Lore translated. (Recovering Energy)",  # 4BB5AE60
    0x742B0696: "Luminoth Lore translated. (Sanctuary Falls)",  # A2406387
    0xEFBA4480: "Luminoth Lore translated. (Saving Aether)",  # 02FC3717
    0xF5535CEA: "Luminoth Lore translated. (Shattered Hope)",  # 73342A54
    0x0405EE3F: "Luminoth Lore translated. (The Final Crusade)",  # 5571E89E
    0x45C31C0B: "Luminoth Lore translated. (The Ing Attack)",  # 7448931C
    0x82919C91: "Luminoth Lore translated. (The New Terror)",  # FB628DCB
    0xCF593D9A: "Luminoth Lore translated. (The Sky Temple)",  # 70E5E6DD
    0xA272E58B: "Luminoth Lore translated. (The Stellar Object)",  # DB7B2CED
    0x8E9FCFAE: "Luminoth Lore translated. (The World Warped)",  # EE4732BE
    0xBF77D533: "Luminoth Lore translated. (Torvus Falls)",  # 914F1381
    0xF2BF7438: "Luminoth Lore translated. (Twilight)",  # 47265C0B
}


def create_hints(patches: GamePatches,
                 world_list: WorldList,
                 hide_area: bool,
                 rng: Random,
                 ) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game for item pickups
    :param patches:
    :param world_list:
    :param hide_area: Should the hint include only the world?
    :param rng:
    :return:
    """

    hint_name_creator = HintNameCreator(world_list, hide_area)
    indicies_to_give_a_hint = [
        PickupIndex(24),  # Light Suit
        PickupIndex(43),  # Dark Suit
        PickupIndex(79),  # Dark Visor
        PickupIndex(115),  # Annihilator Beam
    ]

    additional_hints_needed = len(_LORE_SCANS) - len(indicies_to_give_a_hint)
    potential_hints = [
        index
        for index, pickup in patches.pickup_assignment.items()
        if pickup.item_category.is_major_category
    ]
    indicies_to_give_a_hint.extend(potential_hints[:additional_hints_needed])

    additional_hints_needed = len(_LORE_SCANS) - len(indicies_to_give_a_hint)
    if additional_hints_needed > 0:
        indicies_to_give_a_hint.extend([None] * additional_hints_needed)

    rng.shuffle(indicies_to_give_a_hint)

    hints: List[Tuple[int, str]] = []

    for asset_id, index in zip(_LORE_SCANS.keys(), indicies_to_give_a_hint):
        if index is not None:
            pickup = patches.pickup_assignment.get(index)
            if pickup is not None:
                message = "A {pickup} can be found at {node}.".format(
                    pickup=hint_name_creator.item_name(pickup),
                    node=hint_name_creator.index_node_name(index),
                )
            else:
                message = "{node} has nothing.".format(
                    node=hint_name_creator.index_node_name(index),
                )
        else:
            message = "Aether lacks equipment."

        hints.append((asset_id, message))

    return [
        create_simple_logbook_hint(asset_id, message)
        for asset_id, message in hints
    ]


def hide_hints() -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game
    completely useless text.
    :return:
    """

    return [
        create_simple_logbook_hint(asset_id, "Some item was placed somewhere.")
        for asset_id in _LORE_SCANS.keys()
    ]
