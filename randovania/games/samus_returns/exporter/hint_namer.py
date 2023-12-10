from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import LocationFormatter, RelativeAreaFormatter, TemplatedFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.exporter.hints.relative_item_formatter import RelativeItemFormatter
from randovania.game_description import default_database
from randovania.game_description.hint import Hint, HintLocationPrecision

if TYPE_CHECKING:
    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration


def _area_name(region_list: RegionList, pickup_node: PickupNode, hide_region: bool) -> str:
    area = region_list.nodes_to_area(pickup_node)
    if hide_region:
        return area.name
    else:
        return region_list.area_name(area)


class MSRHintNamer(HintNamer):
    location_formatters: dict[HintLocationPrecision, LocationFormatter]

    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        patches = all_patches[players_config.player_index]
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        self.location_formatters = {
            HintLocationPrecision.DETAILED: TemplatedFormatter(
                location_hint_template,
                self,
            ),
            HintLocationPrecision.REGION_ONLY: TemplatedFormatter(
                location_hint_template,
                self,
            ),
            HintLocationPrecision.RELATIVE_TO_AREA: RelativeAreaFormatter(
                patches,
                lambda msg, with_color: msg,
            ),
            HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(
                patches,
                lambda msg, with_color: msg,
                players_config,
            ),
        }

    def format_joke(self, joke: str, with_color: bool) -> str:
        return joke

    def format_player(self, name: str, with_color: bool) -> str:
        return name

    def format_region(self, location: PickupLocation, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = region_list.region_name_from_node(region_list.node_from_pickup_index(location.location), True)
        return result

    def format_area(self, location: PickupLocation, with_region: bool, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = _area_name(region_list, region_list.node_from_pickup_index(location.location), not with_region)
        return result

    def format_location_hint(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        msg = self.location_formatters[hint.precision.location].format(
            game,
            dataclasses.replace(pick_hint, pickup_name=pick_hint.pickup_name),
            hint,
            with_color,
        )
        return f"{msg}\n"

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        return ""

    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        player_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        return ""

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise RuntimeError("Unsupported feature")
