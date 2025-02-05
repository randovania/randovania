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


class MSRHintNamer(HintNamer[None]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: msg,
            players_config,
        )

    @override
    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used for when an item has a guaranteed hint, but is a starting item."""
        if resource.short_name.startswith("Metroid DNA "):
            return f"The Hunter already started with {resource.long_name}"

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

        # TODO: create_guaranteed_hints_for_resources assumes that the resource is used by a singleton pickup, so we
        # patch the name here instead. Fix it there at one point.
        name = resource.long_name
        if resource.short_name.startswith("Metroid DNA "):
            name = "DNA"
        return fmt.format(
            name,
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
    def color_default(self) -> None:
        return None
