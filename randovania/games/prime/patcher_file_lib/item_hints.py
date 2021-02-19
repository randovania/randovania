import collections
import typing
from random import Random
from typing import Dict, Tuple, Optional

from randovania.game_description import node_search
from randovania.game_description.area import Area
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import HintType, HintLocationPrecision, HintItemPrecision, Hint, RelativeDataArea, \
    HintRelativeAreaName, RelativeDataItem, HintDarkTemple
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import LogbookNode, PickupNode
from randovania.game_description.resources import resource_info
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.games.prime import echoes_items
from randovania.games.prime.echoes_items import USELESS_PICKUP_MODEL
from randovania.games.prime.patcher_file_lib.hint_name_creator import LocationHintCreator, create_simple_logbook_hint, \
    color_text, TextColor
from randovania.interface_common.players_configuration import PlayersConfiguration

_JOKE_HINTS = [
    # Guidelines for joke hints:
    # 1. They should clearly be jokes, and not real hints or the result of a bug.
    # 2. They shouldn't reference real-world people.
    # 3. They should be understandable by as many people as possible.
    #
    "By this point in your run, you should have consumed at least 200 mL of water to maintain optimum hydration.",
    "Make sure to collect an Energy Transfer Module; otherwise your run won't be valid!",
    "Adam has not yet authorized the use of this hint.",
    "Back in my day, we didn't need hints!",
    "Hear the words of O-Lir, last Sentinel of the Fortress Temple. May they serve you well.",
    "Warning! Dark Aether's atmosphere is dangerous! Energized Safe Zones don't last forever!",
    "A really important item can be found at - (transmission ends)",
    "Did you know that Bigfoot and Santa Claus exist in the Metroid Prime canon?",
    "I hear. Them. Everywhere. They're coming. Can't sleep. Ever. They'll eat me. Eat.",
    "Space Pirates, strangely, dislike theft.",
    "Power Bomb Expansions are just space hamburgers.",
    "While in Morph Ball mode, press &image=SI,0.70,0.68,D523DE3B; to drop Bombs.",
    "Charge your beam to fire a normal shot when out of ammo.",
    "Movement in Morph Ball mode is faster than unmorphed, even without Boost Ball.",
    "While walking, holding L makes you move faster."
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
_DET_NULL.extend(f"{temple} Key {i}"
                 for i in range(1, 4)
                 for temple in ("Dark Agon", "Dark Torvus", "Ing Hive"))
_DET_NULL.extend(f"Sky Temple Key {i}" for i in range(1, 10))


class Determiner:
    s: str
    supports_title: bool

    def __init__(self, s, supports_title: bool = True):
        self.s = s
        self.supports_title = supports_title

    def __format__(self, format_spec):
        return self.s.__format__(format_spec)

    @property
    def title(self):
        if self.supports_title:
            return self.s.title()
        else:
            return self.s


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
        distance = self._calculate_distance(hint.target, other_area) + hint.precision.relative.distance_offset
        if distance == 1:
            distance_msg = "one room"
        else:
            precise_msg = "exactly " if hint.precision.relative.distance_offset == 0 else "up to "
            distance_msg = f"{precise_msg}{distance} rooms"

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
    def __init__(self, world_list: WorldList, patches: GamePatches, players_config: PlayersConfiguration):
        super().__init__(world_list, patches)
        self.players_config = players_config

    def format(self, determiner: Determiner, pickup: str, hint: Hint) -> str:
        relative = typing.cast(RelativeDataItem, hint.precision.relative)
        index = relative.other_index

        other_area = self.world_list.nodes_to_area(self._index_to_node[index])
        other_name = "".join(_calculate_pickup_hint(self.patches.pickup_assignment, self.world_list,
                                                    relative.precision,
                                                    self.patches.pickup_assignment.get(index),
                                                    self.players_config))

        return self.relative_format(determiner, pickup, hint, other_area, other_name)


def _calculate_pickup_hint(pickup_assignment: PickupAssignment,
                           world_list: WorldList,
                           precision: HintItemPrecision,
                           target: Optional[PickupTarget],
                           players_config: PlayersConfiguration,
                           ) -> Tuple[str, str]:
    """

    :param pickup_assignment:
    :param world_list:
    :param precision:
    :param target:
    :return:
    """
    if target is None:
        target = PickupTarget(
            pickup=PickupEntry(
                name="Energy Transfer Module",
                resources=(ConditionalResources(None, None, ()),),
                model_index=USELESS_PICKUP_MODEL,
                item_category=ItemCategory.ETM,
                broad_category=ItemCategory.ETM,
            ),
            player=players_config.player_index,
        )

    if precision is HintItemPrecision.GENERAL_CATEGORY:
        return target.pickup.item_category.general_details

    elif precision is HintItemPrecision.PRECISE_CATEGORY:
        return target.pickup.item_category.hint_details

    elif precision is HintItemPrecision.BROAD_CATEGORY:
        return target.pickup.broad_category.hint_details

    elif precision is HintItemPrecision.DETAILED:
        return _calculate_determiner(pickup_assignment, target.pickup, world_list), target.pickup.name

    elif precision is HintItemPrecision.NOTHING:
        return "an", "item"

    else:
        raise ValueError(f"Unknown precision: {precision}")


def _calculate_determiner(pickup_assignment: PickupAssignment, pickup: PickupEntry, world_list: WorldList) -> str:
    name_count = collections.defaultdict(int)
    for i in range(world_list.num_pickup_nodes):
        index = PickupIndex(i)
        if index in pickup_assignment:
            pickup_name = pickup_assignment[index].pickup.name
        else:
            pickup_name = "Energy Transfer Module"
        name_count[pickup_name] += 1

    if pickup.name in _DET_NULL:
        determiner = ""
    elif name_count[pickup.name] == 1:
        determiner = "the "
    elif pickup.name in _DET_AN:
        determiner = "an "
    else:
        determiner = "a "

    return determiner


def create_temple_key_hint(all_patches: Dict[int, GamePatches],
                           player_index: int,
                           temple: HintDarkTemple,
                           world_list: WorldList,
                           ) -> str:
    """
    Creates the text for .
    :param all_patches:
    :param player_index:
    :param temple:
    :param world_list:
    :return:
    """
    all_world_names = set()

    _TEMPLE_NAMES = ["Dark Agon Temple", "Dark Torvus Temple", "Hive Temple"]
    temple_index = [HintDarkTemple.AGON_WASTES, HintDarkTemple.TORVUS_BOG,
                    HintDarkTemple.SANCTUARY_FORTRESS].index(temple)
    keys = echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index]

    index_to_node = {
        node.pickup_index: node
        for node in world_list.all_nodes
        if isinstance(node, PickupNode)
    }

    for patches in all_patches.values():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != player_index:
                continue

            resources = resource_info.convert_resource_gain_to_current_resources(target.pickup.resource_gain({}))
            for resource, quantity in resources.items():
                if quantity < 1 or resource.index not in keys:
                    continue

                pickup_node = index_to_node[pickup_index]
                all_world_names.add(world_list.world_name_from_node(pickup_node, True))

    temple_name = color_text(TextColor.ITEM, _TEMPLE_NAMES[temple_index])
    names_sorted = [color_text(TextColor.LOCATION, world) for world in sorted(all_world_names)]
    if len(names_sorted) == 0:
        return f"The keys to {temple_name} are nowhere to be found."
    elif len(names_sorted) == 1:
        return f"The keys to {temple_name} can all be found in {names_sorted[0]}."
    else:
        last = names_sorted.pop()
        front = ", ".join(names_sorted)
        return f"The keys to {temple_name} can be found in {front} and {last}."


def create_message_for_hint(hint: Hint,
                            all_patches: Dict[int, GamePatches],
                            players_config: PlayersConfiguration,
                            hint_name_creator: LocationHintCreator,
                            location_formatters: Dict[HintLocationPrecision, LocationFormatter],
                            world_list: WorldList,
                            ) -> str:
    if hint.hint_type == HintType.JOKE:
        return color_text(TextColor.JOKE, hint_name_creator.create_joke_hint())

    elif hint.hint_type == HintType.RED_TEMPLE_KEY_SET:
        return create_temple_key_hint(all_patches, players_config.player_index, hint.dark_temple, world_list)

    else:
        assert hint.hint_type == HintType.LOCATION
        patches = all_patches[players_config.player_index]
        pickup_target = patches.pickup_assignment.get(hint.target)
        determiner, pickup_name = _calculate_pickup_hint(patches.pickup_assignment,
                                                         world_list,
                                                         hint.precision.item,
                                                         pickup_target,
                                                         players_config)

        use_title_formatting = True
        if hint.precision.include_owner and len(players_config.player_names) > 1:
            target_player = pickup_target.player if pickup_target is not None else players_config.player_index
            determiner = f"{players_config.player_names[target_player]}'s "
            use_title_formatting = False

        return location_formatters[hint.precision.location].format(
            Determiner(determiner, use_title_formatting),
            color_text(TextColor.ITEM, pickup_name),
            hint,
        )


def create_hints(all_patches: Dict[int, GamePatches],
                 players_config: PlayersConfiguration,
                 world_list: WorldList,
                 rng: Random,
                 ) -> list:
    """
    Creates the string patches entries that changes the Lore scans in the game for item pickups
    :param all_patches:
    :param players_config:
    :param world_list:
    :param rng:
    :return:
    """

    hint_name_creator = LocationHintCreator(world_list, rng, _JOKE_HINTS)
    patches = all_patches[players_config.player_index]

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
        HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(world_list, patches, players_config),
    }

    hints_for_asset: Dict[int, str] = {}
    for asset, hint in patches.hints.items():
        hints_for_asset[asset.asset_id] = create_message_for_hint(hint, all_patches, players_config, hint_name_creator,
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
