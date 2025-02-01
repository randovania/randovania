from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Generic, NamedTuple, TypeVar

from randovania.game_description import default_database

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_formatters import LocationFormatter
    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.hint import HintLocationPrecision, LocationHint
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.pickup_index import PickupIndex


class PickupLocation(NamedTuple):
    game: RandovaniaGame
    location: PickupIndex


ColorT = TypeVar("ColorT")


class HintNamer(Generic[ColorT]):
    location_formatters: dict[HintLocationPrecision | HintFeature, LocationFormatter]

    def colorize_text(self, color: ColorT | None, text: str, with_color: bool) -> str:
        return text

    @property
    def color_joke(self) -> ColorT | None:
        return None

    @property
    def color_player(self) -> ColorT | None:
        return None

    @property
    def color_location(self) -> ColorT | None:
        return None

    @property
    def color_item(self) -> ColorT | None:
        return None

    def _area_name(self, region_list: RegionList, pickup_node: PickupNode, hide_region: bool) -> str:
        area = region_list.nodes_to_area(pickup_node)
        if hide_region:
            return area.name
        else:
            return region_list.area_name(area)

    def format_joke(self, joke: str, with_color: bool) -> str:
        return self.colorize_text(self.color_joke, joke, with_color)

    def format_player(self, name: str, with_color: bool) -> str:
        return self.colorize_text(self.color_player, name, with_color)

    def format_region(self, location: PickupLocation, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = region_list.region_name_from_node(region_list.node_from_pickup_index(location.location), True)
        return self.colorize_text(self.color_location, result, with_color)

    def format_area(self, location: PickupLocation, with_region: bool, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = self._area_name(region_list, region_list.node_from_pickup_index(location.location), not with_region)
        return self.colorize_text(self.color_location, result, with_color)

    def format_location_feature(self, feature: HintFeature, with_color: bool) -> str:
        return self.colorize_text(self.color_location, feature.hint_details[1], with_color)

    def format_location_hint(
        self, game: RandovaniaGame, pick_hint: PickupHint, hint: LocationHint, with_color: bool
    ) -> str:
        return self.location_formatters[hint.precision.location].format(
            game,
            dataclasses.replace(
                pick_hint, pickup_name=self.colorize_text(self.color_item, pick_hint.pickup_name, with_color)
            ),
            hint,
            with_color,
        )

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        return f"{self.colorize_text(self.color_item, resource.long_name, with_color)} has no need to be located."

    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        player_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        """Used when for indicating where a given resource can be found."""
        raise NotImplementedError

    # Echoes only
    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise NotImplementedError

    # Helper
    def format_location(self, location: PickupLocation, with_region: bool, with_area: bool, with_color: bool) -> str:
        if with_area:
            return self.format_area(location, with_region=with_region, with_color=with_color)
        elif with_region:
            return self.format_region(location, with_color=with_color)
        else:
            raise ValueError("Both with_region and with_area not not set.")
