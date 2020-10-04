from random import Random
from typing import Dict, Tuple

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintType, HintLocationPrecision, HintItemPrecision
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.games.prime.patcher_file_lib.hint_name_creator import LocationHintCreator, create_simple_logbook_hint, \
    color_text, TextColor

# Guidelines for joke hints:
# 1. They should clearly be jokes, and not real hints or the result of a bug.
# 2. They shouldn't reference real-world people.
# 3. They should be understandable by as many people as possible.
_JOKE_HINTS = [
    "By this point in your run, you should have consumed at least 200 mL of water to maintain optimum hydration.",
    "Make sure to collect an Energy Transfer Module; otherwise your run won't be valid!",
    "Adam has not yet authorized the use of this hint.",
    "Back in my day, we didn't need hints!",
    "Hear the words of O-Lir, last Sentinel of the Fortress Temple. May they serve you well.",
    "Warning! Dark Aether's atmosphere is dangerous! Energized Safe Zones don't last forever!",
    "A really important item can be found at - (transmission ends)",
]

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

_GUARDIAN_NAMES = {
    PickupIndex(43): "Amorbis",
    PickupIndex(79): "Chykka",
    PickupIndex(115): "Quadraxis",
}

_HINT_MESSAGE_TEMPLATES = {
    HintLocationPrecision.KEYBEARER: "The Flying Ing Cache in {node} contains {determiner}{pickup}.",
    HintLocationPrecision.GUARDIAN: "{node} is guarding {determiner}{pickup}.",
    HintLocationPrecision.LIGHT_SUIT_LOCATION: "U-Mos's reward for returning the Sanctuary energy is {determiner}{pickup}.",
    HintLocationPrecision.DETAILED: "{determiner.title}{pickup} can be found in {node}.",
    HintLocationPrecision.WORLD_ONLY: "{determiner.title}{pickup} can be found in {node}.",
}


class Determiner:
    s: str

    def __init__(self, s):
        self.s = s

    def __format__(self, format_spec):
        return self.s.__format__(format_spec)

    @property
    def title(self):
        return self.s.title()


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
    joke_hints = sorted(_JOKE_HINTS)
    rng.shuffle(joke_hints)

    hints_for_asset: Dict[int, str] = {}

    for asset, hint in patches.hints.items():
        if hint.hint_type == HintType.JOKE:
            if not joke_hints:
                joke_hints = sorted(_JOKE_HINTS)
                rng.shuffle(joke_hints)
            message = color_text(TextColor.JOKE, joke_hints.pop())

        else:
            target = patches.pickup_assignment.get(hint.target)

            # Determine location name
            if hint.precision.location == HintLocationPrecision.GUARDIAN:
                node_name = color_text(TextColor.GUARDIAN, _GUARDIAN_NAMES[hint.target])

            else:
                node_name = color_text(TextColor.LOCATION, hint_name_creator.index_node_name(
                    hint.target,
                    hint.precision.location == HintLocationPrecision.WORLD_ONLY
                ))

            # Determine pickup name
            if target is not None:
                is_joke, determiner, pickup_name = _calculate_pickup_hint(
                    hint.precision.item,
                    _calculate_determiner(patches.pickup_assignment, target.pickup),
                    target.pickup,
                )
            else:
                is_joke = False
                determiner = "the " if len(patches.pickup_assignment) == 118 else "an "
                pickup_name = "Energy Transfer Module"

            pickup_name = color_text(TextColor.JOKE if is_joke else TextColor.ITEM, pickup_name)
            message = _HINT_MESSAGE_TEMPLATES[hint.precision.location].format(determiner=Determiner(determiner),
                                                                              pickup=pickup_name,
                                                                              node=node_name)
        hints_for_asset[asset.asset_id] = message

    return [
        create_simple_logbook_hint(
            logbook_node.string_asset_id,
            hints_for_asset.get(logbook_node.string_asset_id, "Someone forgot to leave a message."),
        )
        for logbook_node in world_list.all_nodes
        if isinstance(logbook_node, LogbookNode)
    ]


def _calculate_pickup_hint(precision: HintItemPrecision,
                           determiner: str,
                           pickup: PickupEntry,
                           ) -> Tuple[bool, str, str]:
    if precision is HintItemPrecision.GENERAL_CATEGORY:
        if pickup.item_category.is_major_category:
            return False, "a ", "major upgrade"
        elif pickup.item_category.is_key:
            return False, "a ", "Dark Temple Key"
        else:
            return False, "an ", "expansion"

    elif precision is HintItemPrecision.PRECISE_CATEGORY:
        details = pickup.item_category.hint_details
        return False, details[0], details[1]

    else:
        return False, determiner, pickup.name


def _calculate_determiner(pickup_assignment: PickupAssignment, pickup: PickupEntry) -> str:
    if pickup.name in _DET_NULL:
        determiner = ""
    elif tuple(pickup_entry.pickup.name for pickup_entry in pickup_assignment.values()).count(pickup.name) == 1:
        determiner = "the "
    elif pickup.name in _DET_AN:
        determiner = "an "
    else:
        determiner = "a "

    return determiner


def hide_hints(world_list: WorldList) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game
    completely useless text.
    :return:
    """

    return [create_simple_logbook_hint(logbook_node.string_asset_id, "Some item was placed somewhere.")
            for logbook_node in world_list.all_nodes if isinstance(logbook_node, LogbookNode)]
