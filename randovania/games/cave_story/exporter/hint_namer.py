from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_formatters import TemplatedFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description.hint import HintLocationPrecision

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration


class CSHintNamer(HintNamer[None]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        patches = all_patches[players_config.player_index]

        location_hint_template = "{{start}} {determiner}{pickup} {{mid}} in {node}."
        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: msg,
            players_config,
        )

        self.location_formatters.update(
            {
                HintLocationPrecision.MALCO: TemplatedFormatter(
                    "BUT ALL I KNOW HOW TO DO IS MAKE {determiner.upper}{pickup}...", self, upper_pickup=True
                ),
                HintLocationPrecision.JENKA: TemplatedFormatter(
                    "perhaps I'll give you {determiner}{pickup} in return...", self
                ),
                HintLocationPrecision.LITTLE: TemplatedFormatter(
                    "He was exploring the island with {determiner}{pickup}...", self
                ),
                HintLocationPrecision.NUMAHACHI: TemplatedFormatter("{determiner.capitalize}{pickup}.", self),
            }
        )

    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        player_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        # TODO
        raise NotImplementedError

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise RuntimeError("Unsupported function")
