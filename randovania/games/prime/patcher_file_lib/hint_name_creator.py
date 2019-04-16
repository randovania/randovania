from typing import Dict

from randovania.game_description.node import PickupNode
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList


def _color_text_as_red(text: str) -> str:
    return "&push;&main-color=#a84343;{}&pop;".format(text)


class HintNameCreator:
    world_list: WorldList
    hide_area: bool
    index_to_node: Dict[PickupIndex, PickupNode]

    def __init__(self, world_list: WorldList, hide_area: bool):
        self.world_list = world_list
        self.hide_area = hide_area
        self.index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def index_node_name(self, pickup_index: PickupIndex) -> str:
        return self.node_name(self.index_to_node[pickup_index])

    def node_name(self, pickup_node: PickupNode) -> str:
        return _color_text_as_red(
            self.world_list.nodes_to_world(pickup_node).name
            if self.hide_area else
            self.world_list.area_name(
                self.world_list.nodes_to_area(pickup_node),
                " - "
            )
        )

    def item_name(self, pickup: PickupEntry) -> str:
        return _color_text_as_red(pickup.name)


def create_simple_logbook_hint(asset_id: int, hint: str) -> dict:
    return {
        "asset_id": asset_id,
        "strings": [hint, "", hint],
    }
