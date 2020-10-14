import typing
from random import Random
from typing import Dict, Tuple, Optional

from randovania.game_description import node_search
from randovania.game_description.area import Area
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintType, HintLocationPrecision, HintItemPrecision, Hint, RelativeDataArea, \
    HintRelativeAreaName, RelativeDataItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, PickupNode
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


class Determiner:
    s: str

    def __init__(self, s):
        self.s = s

    def __format__(self, format_spec):
        return self.s.__format__(format_spec)

    @property
    def title(self):
        return self.s.title()


class LocationFormatter:
    def format(self, determiner: Determiner, pickup_name: str, hint: Hint) -> str:
        raise NotImplementedError()


class GuardianFormatter(LocationFormatter):
    _GUARDIAN_NAMES = {
        PickupIndex(43): "Amorbis",
        PickupIndex(79): "Chykka",
        PickupIndex(115): "Quadraxis",
    }

    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        guardian = color_text(TextColor.GUARDIAN, self._GUARDIAN_NAMES[hint.target])
        return f"{guardian} is guarding {determiner}{pickup}."


class TemplatedFormatter(LocationFormatter):
    def __init__(self, template: str, hint_name_creator: LocationHintCreator):
        self.template = template
        self.hint_name_creator = hint_name_creator

    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        node_name = color_text(TextColor.LOCATION, self.hint_name_creator.index_node_name(
            hint.target,
            hint.precision.location == HintLocationPrecision.WORLD_ONLY
        ))
        return self.template.format(determiner=determiner,
                                    pickup=pickup,
                                    node=node_name)


class RelativeFormatter(LocationFormatter):
    def __init__(self, world_list: WorldList, patches: GamePatches):
        self.world_list = world_list
        self.patches = patches
        self._index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def _calculate_distance(self, source_location: PickupIndex, target: Area) -> int:
        source = self._index_to_node[source_location]
        return node_search.distances_to_node(self.world_list, source,
                                             patches=self.patches, ignore_elevators=False)[target]

    def relative_format(self, determiner: Determiner, pickup: str, hint: Hint, other_area: Area, other_name: str,
                        ) -> str:
        distance = self._calculate_distance(hint.target, other_area)
        if distance > 1:
            precise_msg = "exactly " if hint.precision.relative.precise_distance else "up to "
            distance_msg = f"{precise_msg}{distance} rooms"
        else:
            distance_msg = "one room"

        return (f"{determiner.title}{pickup} can be found "
                f"{color_text(TextColor.LOCATION, distance_msg)} away from {other_name}.")


class RelativeAreaFormatter(RelativeFormatter):
    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        relative = typing.cast(RelativeDataArea, hint.precision.relative)
        other_area = self.world_list.area_by_area_location(relative.area_location)

        if relative.precision == HintRelativeAreaName.NAME:
            other_name = self.world_list.area_name(other_area)
        elif relative.precision == HintRelativeAreaName.FEATURE:
            raise NotImplementedError("HintRelativeAreaName.FEATURE not implemented")
        else:
            raise ValueError(f"Unknown precision: {relative.precision}")

        return self.relative_format(determiner, pickup, hint, other_area, other_name)


class RelativeItemFormatter(RelativeFormatter):
    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        relative = typing.cast(RelativeDataItem, hint.precision.relative)
        index = relative.other_index

        other_area = self.world_list.nodes_to_area(self._index_to_node[index])
        other_name = "".join(_calculate_pickup_hint(self.patches.pickup_assignment, self.world_list,
                                                    relative.precision,
                                                    self.patches.pickup_assignment.get(index)))

        return self.relative_format(determiner, pickup, hint, other_area, other_name)


def _calculate_pickup_hint(pickup_assignment: PickupAssignment,
                           world_list: WorldList,
                           precision: HintItemPrecision,
                           target: Optional[PickupTarget],
                           ) -> Tuple[str, str]:
    """

    :param pickup_assignment:
    :param world_list:
    :param precision:
    :param target:
    :return:
    """
    item_category = ItemCategory.ETM if target is None else target.pickup.item_category
    if precision is HintItemPrecision.GENERAL_CATEGORY:
        if item_category.is_major_category:
            return "a ", "major upgrade"
        elif item_category.is_key:
            return "a ", "Dark Temple Key"
        else:
            return "an ", "expansion"

    elif precision is HintItemPrecision.PRECISE_CATEGORY:
        details = item_category.hint_details
        return details[0], details[1]

    elif target is None:
        if len(pickup_assignment) == world_list.num_pickup_nodes - 1:
            determiner = "the "
        else:
            determiner = "an "
        return determiner, "Energy Transfer Module"
    else:
        return _calculate_determiner(pickup_assignment, target.pickup), target.pickup.name


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


def create_message_for_hint(hint: Hint,
                            patches: GamePatches,
                            hint_name_creator: LocationHintCreator,
                            location_formatters: Dict[HintLocationPrecision, LocationFormatter],
                            world_list: WorldList,
                            ) -> str:
    if hint.hint_type == HintType.JOKE:
        return color_text(TextColor.JOKE, hint_name_creator.create_joke_hint())

    else:
        determiner, pickup_name = _calculate_pickup_hint(patches.pickup_assignment,
                                                         world_list,
                                                         hint.precision.item,
                                                         patches.pickup_assignment.get(hint.target))
        return location_formatters[hint.precision.location].format(
            Determiner(determiner),
            color_text(TextColor.ITEM, pickup_name),
            hint,
        )


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

    hint_name_creator = LocationHintCreator(world_list, rng, _JOKE_HINTS)

    location_formatters: Dict[HintLocationPrecision, LocationFormatter] = {
        HintLocationPrecision.KEYBEARER: TemplatedFormatter(
            "The Flying Ing Cache in {node} contains {determiner}{pickup}.", hint_name_creator),
        HintLocationPrecision.GUARDIAN: GuardianFormatter(),
        HintLocationPrecision.LIGHT_SUIT_LOCATION: TemplatedFormatter(
            "U-Mos's reward for returning the Sanctuary energy is {determiner}{pickup}.", hint_name_creator),
        HintLocationPrecision.DETAILED: TemplatedFormatter("{determiner.title}{pickup} can be found in {node}.",
                                                           hint_name_creator),
        HintLocationPrecision.WORLD_ONLY: TemplatedFormatter("{determiner.title}{pickup} can be found in {node}.",
                                                             hint_name_creator),
        HintLocationPrecision.RELATIVE_TO_AREA: RelativeAreaFormatter(world_list, patches),
        HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(world_list, patches),
    }

    hints_for_asset: Dict[int, str] = {}
    for asset, hint in patches.hints.items():
        hints_for_asset[asset.asset_id] = create_message_for_hint(hint, patches, hint_name_creator,
                                                                  location_formatters, world_list)

    return [
        create_simple_logbook_hint(
            logbook_node.string_asset_id,
            hints_for_asset.get(logbook_node.string_asset_id, "Someone forgot to leave a message."),
        )
        for logbook_node in world_list.all_nodes
        if isinstance(logbook_node, LogbookNode)
    ]


def hide_hints(world_list: WorldList) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game
    completely useless text.
    :return:
    """

    return [create_simple_logbook_hint(logbook_node.string_asset_id, "Some item was placed somewhere.")
            for logbook_node in world_list.all_nodes if isinstance(logbook_node, LogbookNode)]
