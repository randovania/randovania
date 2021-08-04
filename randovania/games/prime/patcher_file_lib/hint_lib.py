from enum import Enum
from typing import Dict, Optional

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.interface_common.players_configuration import PlayersConfiguration


class TextColor(Enum):
    GUARDIAN = "#FF3333"
    ITEM = "#FF6705B3"
    PRIME1_ITEM = "#c300ff"
    JOKE = "#45F731"
    LOCATION = "#FF3333"
    PRIME1_LOCATION = "#89a1ff"
    PLAYER = "#d4cc33"


def color_text(color: TextColor, text: str):
    return f"&push;&main-color={color.value};{text}&pop;"


def create_simple_logbook_hint(asset_id: int, hint: str) -> dict:
    return {
        "asset_id": asset_id,
        "strings": [hint, "", hint],
    }


class AreaNamer:
    world_list: WorldList
    index_to_node: Dict[PickupIndex, PickupNode]

    def __init__(self, world_list: WorldList):
        self.world_list = world_list

        self.index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def location_name(self, pickup_index: PickupIndex, hide_area: bool,
                      color: Optional[TextColor] = TextColor.LOCATION) -> str:
        result = self.node_name(self.index_to_node[pickup_index], hide_area)
        if color is not None:
            return color_text(color, result)
        return result

    def node_name(self, pickup_node: PickupNode, hide_area: bool) -> str:
        if hide_area:
            return self.world_list.world_name_from_node(pickup_node, True)
        else:
            return self.world_list.area_name(self.world_list.nodes_to_area(pickup_node))


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


def player_determiner(players_config: PlayersConfiguration, player: int,
                      color: TextColor = TextColor.PLAYER) -> Determiner:
    return Determiner(
        "{}'s ".format(color_text(color, players_config.player_names[player])),
        False
    )
