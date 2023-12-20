from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.hints.hint_formatters import LocationFormatter, TemplatedFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description import default_database
from randovania.game_description.hint import Hint, HintLocationPrecision

if TYPE_CHECKING:
    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_patches import GamePatches
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.players_configuration import PlayersConfiguration


def _area_name(region_list: RegionList, pickup_node: PickupNode, hide_region: bool) -> str:
    area = region_list.nodes_to_area(pickup_node)
    return region_list.area_name(area)


class MSRHintNamer(HintNamer):
    location_formatters: dict[HintLocationPrecision, LocationFormatter]

    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        self.location_formatters = {
            HintLocationPrecision.REGION_ONLY: TemplatedFormatter(
                location_hint_template,
                self,
            )
        }

    def format_region(self, location: PickupLocation, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = region_list.region_name_from_node(region_list.node_from_pickup_index(location.location), True)
        return result

    def format_area(self, location: PickupLocation, with_region: bool, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = _area_name(region_list, region_list.node_from_pickup_index(location.location), not with_region)
        return result

    def format_location_hint(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        assert hint.precision is not None
        msg = self.location_formatters[hint.precision.location].format(
            game,
            dataclasses.replace(pick_hint, pickup_name=pick_hint.pickup_name),
            hint,
            with_color,
        )
        return f"{msg}\n"

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise RuntimeError("Unsupported feature")
