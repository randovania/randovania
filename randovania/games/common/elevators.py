from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription


def get_elevator_name_or_default(game: GameDescription, node_location: NodeIdentifier, default: str) -> str:
    node = game.region_list.node_by_identifier(node_location)
    if isinstance(node, DockNode) and node.ui_custom_name:
        return node.ui_custom_name
    else:
        return default


def get_elevator_or_area_name(
    game: GameDescription, region_list: RegionList, node_location: NodeIdentifier, include_world_name: bool
) -> str:
    return _get_elevator_or_area_name(game, region_list, node_location, include_world_name)


def _get_elevator_or_area_name(
    game: GameDescription,
    region_list: RegionList,
    node_location: NodeIdentifier,
    include_world_name: bool,
) -> str:
    node = game.region_list.node_by_identifier(node_location)
    if isinstance(node, DockNode) and node.ui_custom_name:
        return node.ui_custom_name
    else:
        area = region_list.area_by_area_location(node_location.area_identifier)
        if include_world_name:
            return region_list.area_name(area)
        else:
            return area.name
