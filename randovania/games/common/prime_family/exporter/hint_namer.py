from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration


class PrimeFamilyHintNamer(HintNamer[str]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]

        location_hint_template = "{determiner.title}{pickup} can be found in {node}."
        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: self.colorize_text(self.color_location, msg, with_color),
            players_config,
        )

    @override
    @classmethod
    def colorize_text(cls, color: str, text: str, with_color: bool):
        if with_color:
            return f"&push;&main-color={color};{text}&pop;"
        else:
            return text

    @override
    def format_guaranteed_resource(
        self,
        resource: ItemResourceInfo,
        world_name: str | None,
        location: PickupLocation,
        hide_area: bool,
        with_color: bool,
    ) -> str:
        determiner = ""
        if world_name is not None:
            determiner = self.format_world(world_name, with_color=with_color) + "'s "

        resource_color = self.colorize_text(self.color_item, resource.long_name, with_color)
        location_color = self.format_location(
            location, with_region=True, with_area=not hide_area, with_color=with_color
        )
        return f"{resource_color} is located in {determiner}{location_color}."
