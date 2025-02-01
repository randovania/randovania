from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation

if TYPE_CHECKING:
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration


def _area_name(region_list: RegionList, pickup_node: PickupNode, hide_region: bool) -> str:
    area = region_list.nodes_to_area(pickup_node)
    if hide_region:
        return area.name
    else:
        return region_list.area_name(area)


def colorize_text(color: str, text: str, with_color: bool):
    if with_color:
        return f"&push;&main-color={color};{text}&pop;"
    else:
        return text


class PrimeFamilyHintNamer(HintNamer[str]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        patches = all_patches[players_config.player_index]

        location_hint_template = "{determiner.title}{pickup} can be found in {node}."
        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: colorize_text(self.color_location, msg, with_color),
            players_config,
        )

    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        player_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        determiner = ""
        if player_name is not None:
            determiner = self.format_player(player_name, with_color=with_color) + "'s "

        resource_color = colorize_text(self.color_item, resource.long_name, with_color)
        location_color = self.format_location(
            location, with_region=True, with_area=not hide_area, with_color=with_color
        )
        return f"{resource_color} is located in {determiner}{location_color}."

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise NotImplementedError

    @property
    def color_joke(self) -> str:
        raise NotImplementedError

    @property
    def color_item(self) -> str:
        raise NotImplementedError

    @property
    def color_player(self) -> str:
        raise NotImplementedError

    @property
    def color_location(self) -> str:
        raise NotImplementedError
