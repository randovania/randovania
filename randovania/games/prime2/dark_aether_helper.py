from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.common.elevators import NodeListGrouping

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.region import Region


def is_region_light(region: Region) -> bool:
    """
    Checks if the given Region is in Light Aether.
    """
    return "asset_id" in region.extra


def get_counterpart_name(region: Region) -> str:
    """
    Gets the name of the Light/Dark counterpart region
    """
    return region.extra["associated_region"]


def region_list_grouping(region_list: Iterable[Region]) -> list[list[Region]]:
    """
    Given a list of region, creates a list of Regions pairs, where each pair is the Light World
    and Dark World of each one.
    """
    new_groups: list[list[Region]] = []
    group_index = {}
    dark_regions = []

    for region in region_list:
        if is_region_light(region):
            group_index[region.name] = len(new_groups)
            new_groups.append([region])
        else:
            dark_regions.append(region)

    for region in dark_regions:
        new_groups[group_index[get_counterpart_name(region)]].append(region)

    return new_groups


def wrap_node_list_grouping(grouping: NodeListGrouping) -> NodeListGrouping:
    """
    Creates a new NodeListGrouping using region_list_grouping.
    """
    return NodeListGrouping(
        region_list_grouping(region_group[0] for region_group in grouping.region_groups),
        grouping.areas_by_region,
        grouping.nodes_by_area,
    )
