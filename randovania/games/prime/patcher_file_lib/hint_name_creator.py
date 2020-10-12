from enum import Enum
from random import Random
from typing import Dict, List

from randovania.game_description.node import PickupNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList


class LocationHintCreator:
    world_list: WorldList
    joke_hints: List[str]
    index_to_node: Dict[PickupIndex, PickupNode]

    def __init__(self, world_list: WorldList, rng: Random, base_joke_hints: List[str]):
        self.world_list = world_list
        self.rng = rng
        self.base_joke_hints = base_joke_hints
        self.joke_hints = []

        self.index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def index_node_name(self, pickup_index: PickupIndex, hide_area: bool) -> str:
        return self.node_name(self.index_to_node[pickup_index], hide_area)

    def node_name(self, pickup_node: PickupNode, hide_area: bool) -> str:
        if hide_area:
            return self.world_list.world_name_from_node(pickup_node, True)
        else:
            return self.world_list.area_name(self.world_list.nodes_to_area(pickup_node))

    def create_joke_hint(self) -> str:
        if not self.joke_hints:
            self.joke_hints = sorted(self.base_joke_hints)
            self.rng.shuffle(self.joke_hints)
        return self.joke_hints.pop()


class TextColor(Enum):
    GUARDIAN = "#FF3333"
    ITEM = "#FF6705B3"
    JOKE = "#45F731"
    LOCATION = "#FF3333"


def color_text(color: TextColor, text: str):
    return f"&push;&main-color={color.value};{text}&pop;"


def create_simple_logbook_hint(asset_id: int, hint: str) -> dict:
    return {
        "asset_id": asset_id,
        "strings": [hint, "", hint],
    }
