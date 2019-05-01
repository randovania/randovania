from random import Random
from typing import Dict, Tuple, List

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintType, HintLocationPrecision, HintItemPrecision, Hint
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world_list import WorldList
from randovania.games.prime.patcher_file_lib.hint_name_creator import LocationHintCreator, create_simple_logbook_hint, \
    color_as_joke, color_text_as_red

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

_PRIME_1_ITEMS = [
    "Varia Suit",
    "Wave Beam",
    "Thermal Visor",
    "Wavebuster",
    "Ice Beam",
    "Gravity Suit",
    "X-Ray Visor",
    "Ice Spreader",
    "Plasma Beam",
    "Flamethrower",
    "Phazon Suit",
]

_PRIME_3_ITEMS = [
    "Grapple Lasso",
    "PED Suit",
    "Grapple Swing",
    "Ice Missile",
    "Ship Missile Launcher",
    "Hyper Ball",
    "Plasma Beam",
    "Ship Grapple Beam",
    "Hyper Missile",
    "X-Ray Visor",
    "Grapple Voltage",
    "Hazard Shield",
    "Nova Beam",
    "Hyper Grapple",
]

_JOKE_HINTS = [
    "Did you remember to check Trial Tunnel?",
    ("By this point in your playthrough, you should have consumed at least "
     "200mL of water to maintain optimum hydration."),
    "Make sure to collect an ETM, otherwise your run isn't valid.",
    "You're not authorized to view this hint.",
]

_PRIME_1_LOCATIONS = [
    "Hive Totem",
    "Ruined Shrine",
    "Burn Dome",
    "Sunchamber",
    "Quarantine Cave",
    "Gravity Chamber",
    "Elite Research",
    "Life Grove",
    "Phendrana Shorelines",
    "Plasma Processing",
    "Elite Quarters",

]

_PRIME_3_LOCATIONS = [
    "Docking Hub Alpha",
    "Command Vault",
    "Proving Grounds",
    "Temple of Bryyo",
]

_DET_AN = [
    "Annihilator Beam",
    "Amber Translator",
    "Echo Visor",
    "Emerald Translator",
    "Energy Transfer Module",
    "Energy Tank",
]

_DET_NULL = []
for i in range(1, 4):
    _DET_NULL.extend([f"Dark Agon Key {i}", f"Dark Torvus Key {i}", f"Ing Hive Key {i}"])
for i in range(1, 10):
    _DET_NULL.append(f"Sky Temple Key {i}")


def _is_total_joke(hint: Hint) -> bool:
    return hint.location_precision == HintLocationPrecision.WRONG_GAME and hint.item_precision == HintItemPrecision.WRONG_GAME


def create_hints(patches: GamePatches,
                 world_list: WorldList,
                 rng: Random,
                 ) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game for item pickups
    :param patches:
    :param world_list:
    :param rng:
    :return:
    """

    hint_name_creator = LocationHintCreator(world_list)
    joke_items = list(set(_PRIME_1_ITEMS) | set(_PRIME_3_ITEMS))
    joke_locations = list(set(_PRIME_3_LOCATIONS))

    rng.shuffle(joke_items)
    rng.shuffle(joke_locations)

    hints_for_asset: Dict[int, str] = {}

    for asset, hint in patches.hints.items():
        if _is_total_joke(hint):
            message = color_as_joke(rng.choice(_JOKE_HINTS))

        elif hint.hint_type == HintType.LOCATION:
            pickup = patches.pickup_assignment.get(hint.target)

            if hint.location_precision == HintLocationPrecision.WRONG_GAME:
                node_name = color_as_joke(joke_locations.pop() if joke_locations else "an unknown location")
            else:
                node_name = color_text_as_red(hint_name_creator.index_node_name(
                    hint.target,
                    hint.location_precision != HintLocationPrecision.DETAILED
                ))

            if pickup is not None:
                is_joke, determiner, pickup_name = _calculate_pickup_hint(hint.item_precision,
                                                                          _calculate_determiner(
                                                                              patches.pickup_assignment,
                                                                              pickup),
                                                                          pickup,
                                                                          joke_items)
            else:
                is_joke = False
                determiner = "The " if len(patches.pickup_assignment) == 118 else "An "
                pickup_name = "Energy Transfer Module"

            message = "{determiner}{pickup} can be found at {node}.".format(
                determiner=determiner,
                pickup=color_as_joke(pickup_name) if is_joke else color_text_as_red(pickup_name),
                node=node_name,
            )
        else:
            message = "This kind of hint should never happen."

        hints_for_asset[asset.asset_id] = message

    return [
        create_simple_logbook_hint(
            asset_id,
            hints_for_asset.get(asset_id, "Someone forgot to leave a message."))
        for asset_id in _LORE_SCANS
    ]


def _calculate_pickup_hint(precision: HintItemPrecision,
                           determiner: str,
                           pickup: PickupEntry,
                           joke_items: List[str],
                           ) -> Tuple[bool, str, str]:
    if precision == HintItemPrecision.WRONG_GAME:
        return True, "The ", joke_items.pop()

    elif precision == HintItemPrecision.GENERAL_CATEGORY:
        if pickup.item_category.is_major_category:
            return False, "A ", "major item"
        elif pickup.item_category.is_key:
            return False, "A ", "key"
        else:
            return False, "An ", "expansion"

    elif precision == HintItemPrecision.PRECISE_CATEGORY:
        details = pickup.item_category.hint_details
        return False, details[0], details[1]

    else:
        return False, determiner, pickup.name


def _calculate_determiner(pickup_assignment: PickupAssignment,
                          pickup: PickupEntry,
                          ) -> str:
    if pickup.name in _DET_NULL:
        determiner = ""
    elif tuple(pickup_entry.name for pickup_entry in pickup_assignment.values()).count(pickup.name) == 1:
        determiner = "The "
    elif pickup.name in _DET_AN:
        determiner = "An "
    else:
        determiner = "A "

    return determiner


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
