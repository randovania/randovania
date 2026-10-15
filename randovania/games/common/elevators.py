from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode

if TYPE_CHECKING:
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_description import GameDescription


def get_elevator_name_or_default(game: GameDescription, node_location: NodeIdentifier, default: str) -> str:
    node = game.region_list.node_by_identifier(node_location)
    if isinstance(node, DockNode) and node.ui_custom_name:
        return node.ui_custom_name
    else:
        return default


def get_elevator_or_area_name(
    node: Node,
    include_region_name: bool,
) -> str:
    if isinstance(node, DockNode) and node.ui_custom_name:
        return node.ui_custom_name
    else:
        if include_region_name:
            return f"{node.identifier.region} - {node.identifier.area}"
        else:
            return node.identifier.area


class NodeListGrouping(typing.NamedTuple):
    region_groups: list[list[Region]]
    areas_by_region: dict[str, list[Area]]
    nodes_by_area: dict[AreaIdentifier, list[Node]]
