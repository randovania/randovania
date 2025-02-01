from enum import Enum

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.interface_common.players_configuration import PlayersConfiguration


class AM2RColor(Enum):
    WHITE = "{white}"
    YELLOW = "{yellow}"
    RED = "{red}"
    PINK = "{fuchsia}"
    GREEN = "{lime}"
    BLUE = "{aqua}"


class AM2RHintNamer(HintNamer[AM2RColor]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        patches = all_patches[players_config.player_index]
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: self.colorize_text(self.color_location, msg, with_color),
            players_config,
        )

    def colorize_text(color: AM2RColor, text: str, with_color: bool) -> str:
        if with_color:
            return f"{color.value}{text}{AM2RColor.WHITE.value}"
        else:
            return text

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        if resource.short_name.startswith("Metroid DNA "):
            return f"The Hunter already started with {resource.long_name}"

        return super().format_resource_is_starting(resource, with_color)

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

        fmt = "{} is located in {}{}."
        location_name = self.format_location(location, with_region=True, with_area=not hide_area, with_color=with_color)

        # TODO: create_guaranteed_hints_for_resources assumes that the resource is used by a singleton pickup, so we
        # patch the name here instead. Fix it there at one point.
        name = resource.long_name
        if resource.short_name.startswith("Metroid DNA "):
            name = "Metroid DNA"
        return fmt.format(
            self.colorize_text(self.color_item, name, with_color),
            determiner,
            location_name,
        )

    @property
    def color_joke(self) -> AM2RColor:
        return AM2RColor.GREEN

    @property
    def color_player(self) -> AM2RColor:
        return AM2RColor.PINK

    @property
    def color_location(self) -> AM2RColor:
        return AM2RColor.BLUE

    @property
    def color_item(self) -> AM2RColor:
        return AM2RColor.YELLOW
