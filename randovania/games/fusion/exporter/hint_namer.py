from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, override

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation

if TYPE_CHECKING:
    from randovania.exporter.hints.pickup_hint import PickupHint
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint import LocationHint
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration


class FusionColor(Enum):
    RESET = "[/COLOR]"
    WHITE = "[COLOR=0]"
    RED = "[COLOR=1]"
    PINK = "[COLOR=2]"
    YELLOW = "[COLOR=3]"
    GREEN = "[COLOR=4]"
    INDIGO = "[COLOR=5]"  # Poor readability
    TEAL = "[COLOR=6]"


class FusionHintNamer(HintNamer[FusionColor]):
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
    def colorize_text(cls, color: FusionColor, text: str, with_color: bool) -> str:
        if with_color:
            return f"{color.value}{text}{FusionColor.RESET.value}"
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

        fmt = "{} is located in {}{}."
        location_name = self.format_location(location, with_region=True, with_area=not hide_area, with_color=with_color)

        return fmt.format(
            self.colorize_text(self.color_item, resource.long_name, with_color),
            determiner,
            location_name,
        )

    @override
    def format_location_hint(
        self, game: RandovaniaGame, pick_hint: PickupHint, hint: LocationHint, with_color: bool
    ) -> str:
        msg = super().format_location_hint(game, pick_hint, hint, with_color)
        return f"{msg}\n"

    @override
    @property
    def color_joke(self) -> FusionColor:
        return FusionColor.GREEN

    @override
    @property
    def color_item(self) -> FusionColor:
        return FusionColor.YELLOW

    @override
    @property
    def color_world(self) -> FusionColor:
        return FusionColor.RED

    @override
    @property
    def color_location(self) -> FusionColor:
        return FusionColor.PINK
