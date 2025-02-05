from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, override

from randovania.exporter.hints.basic_hint_formatters import basic_hint_formatters
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.game_description import default_database
from randovania.games.dread.layout.dread_configuration import DreadConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.interface_common.players_configuration import PlayersConfiguration

# {c0}	White	(Default)
# {c1}	Yellow
# {c2}	Red
# {c3}	Pink
# {c4}	Green
# {c5}	Blue
# {c6}	UI Active	(Light blue)
# {c7}	UI Inactive	(Dim blue)


class DreadColor(Enum):
    WHITE = "{c0}"
    YELLOW = "{c1}"
    RED = "{c2}"
    PINK = "{c3}"
    GREEN = "{c4}"
    BLUE = "{c5}"
    LIGHT_BLUE = "{c6}"
    DIM_BLUE = "{c7}"


class DreadHintNamer(HintNamer[DreadColor]):
    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        super().__init__(all_patches, players_config)

        patches = all_patches[players_config.player_index]
        location_hint_template = "{determiner.title}{pickup} can be found in {node}."

        if isinstance(patches.configuration, DreadConfiguration) and patches.configuration.april_fools_hints:
            location_hint_template = "|".join(
                ["Can you guess where {determiner}{pickup} goes?", "That's right! It goes in the {node} hole!"]
            )

        self.location_formatters = basic_hint_formatters(
            self,
            location_hint_template,
            patches,
            lambda msg, with_color: self.colorize_text(self.color_location, msg, with_color),
            players_config,
        )

    @override
    @classmethod
    def colorize_text(cls, color: DreadColor, text: str, with_color: bool) -> str:
        if with_color:
            return f"{color.value}{text}{DreadColor.WHITE.value}"
        else:
            return text

    @override
    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        if resource.short_name.startswith("Artifact"):
            return ""

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

        region_list = default_database.game_description_for(location.game).region_list
        node = region_list.node_from_pickup_index(location.location)
        if (boss_hint_name := node.extra.get("boss_hint_name")) is not None:
            fmt = "{} is guarded by {}{}."
            location_name = self.colorize_text(DreadColor.RED, boss_hint_name, with_color)

        return fmt.format(
            self.colorize_text(self.color_item, resource.long_name, with_color),
            determiner,
            location_name,
        )

    @override
    @property
    def color_joke(self) -> DreadColor:
        return DreadColor.GREEN

    @override
    @property
    def color_item(self) -> DreadColor:
        return DreadColor.YELLOW

    @override
    @property
    def color_world(self) -> DreadColor:
        return DreadColor.PINK

    @override
    @property
    def color_location(self) -> DreadColor:
        return DreadColor.BLUE
