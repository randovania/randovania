from __future__ import annotations

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


class HuntersHintNamer(HintNamer[None]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]
        location_hint_template = "{determiner.title.upper()}{pickup.upper()} can be found in {node.upper()}."

        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: self.colorize_text(self.color_location, msg, with_color),
            players_config,
        )

    @override
    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used for when an item has a guaranteed hint, but is a starting item."""
        if resource.short_name.startswith("Octolith "):
            return f"the HUNTER already started with {resource.long_name.upper()}."

        return super().format_resource_is_starting(resource, with_color)

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
            self.colorize_text(self.color_item, resource.long_name, with_color).upper(),
            determiner.upper(),
            location_name.upper(),
        )

    @override
    def format_location_hint(
        self, game: RandovaniaGame, pick_hint: PickupHint, hint: LocationHint, with_color: bool
    ) -> str:
        msg = super().format_location_hint(game, pick_hint, hint, with_color)
        return f"{msg}\n"

    @override
    @property
    def color_default(self) -> None:
        return None
