from typing import Dict

from randovania.game_description.node import PickupNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world_list import WorldList


class LocationHintCreator:
    world_list: WorldList
    index_to_node: Dict[PickupIndex, PickupNode]

    def __init__(self, world_list: WorldList):
        self.world_list = world_list
        self.index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def index_node_name(self, pickup_index: PickupIndex, hide_area: bool) -> str:
        return self.node_name(self.index_to_node[pickup_index], hide_area)

    def node_name(self, pickup_node: PickupNode, hide_area: bool) -> str:
        if hide_area:
            return self.world_list.nodes_to_world(pickup_node).name
        else:
            return self.world_list.area_name(
                self.world_list.nodes_to_area(pickup_node),
                " - "
            )


def color_text_as_red(text: str) -> str:
    return "&push;&main-color=#a84343;{}&pop;".format(text)


def color_as_joke(text: str) -> str:
    return "&push;&main-color=#45f731;{}&pop;".format(text)


def create_simple_logbook_hint(asset_id: int, hint: str) -> dict:
    return {
        "asset_id": asset_id,
        "strings": [hint, "", hint],
    }
