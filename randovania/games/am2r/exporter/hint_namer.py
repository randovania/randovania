import dataclasses
from enum import Enum

from randovania.exporter.hints.hint_formatters import LocationFormatter, RelativeAreaFormatter, TemplatedFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.exporter.hints.relative_item_formatter import RelativeItemFormatter
from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintLocationPrecision
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration


class AM2RColor(Enum):
    WHITE = "{white}"
    YELLOW = "{yellow}"
    RED = "{red}"
    PINK = "{fuchsia}"
    GREEN = "{lime}"
    BLUE = "{aqua}"


def _area_name(region_list: RegionList, pickup_node: PickupNode, hide_region: bool) -> str:
    area = region_list.nodes_to_area(pickup_node)
    if hide_region:
        return area.name
    else:
        return region_list.area_name(area)


def colorize_text(color: AM2RColor, text: str, with_color: bool) -> str:
    if with_color:
        return f"{color.value}{text}{AM2RColor.WHITE.value}"
    else:
        return text


class AM2RHintNamer(HintNamer):
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
                lambda msg, with_color: colorize_text(self.color_location, msg, with_color),
            ),
            HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(
                patches,
                lambda msg, with_color: colorize_text(self.color_location, msg, with_color),
                players_config,
            ),
        }

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        if resource.short_name.startswith("Metroid DNA "):
            return f"The Hunter already started with {resource.long_name}"

        return f"{colorize_text(self.color_item, resource.long_name, with_color)} has no need to be located."

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
            colorize_text(self.color_item, name, with_color),
            determiner,
            location_name,
        )

    def format_location_hint(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        return self.location_formatters[hint.precision.location].format(
            game,
            dataclasses.replace(
                pick_hint, pickup_name=colorize_text(self.color_item, pick_hint.pickup_name, with_color)
            ),
            hint,
            with_color,
        )

    def format_region(self, location: PickupLocation, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = region_list.region_name_from_node(region_list.node_from_pickup_index(location.location), True)
        return colorize_text(self.color_location, result, with_color)

    def format_area(self, location: PickupLocation, with_region: bool, with_color: bool) -> str:
        region_list = default_database.game_description_for(location.game).region_list
        result = _area_name(region_list, region_list.node_from_pickup_index(location.location), not with_region)
        return colorize_text(self.color_location, result, with_color)

    def format_player(self, name: str, with_color: bool) -> str:
        return colorize_text(self.color_player, name, with_color)

    def format_joke(self, joke: str, with_color: bool) -> str:
        return colorize_text(self.color_joke, joke, with_color)

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
