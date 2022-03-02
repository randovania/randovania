import dataclasses
from typing import Optional

from randovania.exporter.hints.hint_formatters import LocationFormatter, TemplatedFormatter, RelativeAreaFormatter
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.exporter.hints.relative_item_formatter import RelativeItemFormatter
from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintLocationPrecision
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import PlayersConfiguration


def _area_name(world_list: WorldList, pickup_node: PickupNode, hide_world: bool) -> str:
    area = world_list.nodes_to_area(pickup_node)
    if hide_world:
        return area.name
    else:
        return world_list.area_name(area)


def colorize_text(color: str, text: str, with_color: bool):
    if with_color:
        return f"&push;&main-color={color};{text}&pop;"
    else:
        return text


class PrimeFamilyHintNamer(HintNamer):
    location_formatters: dict[HintLocationPrecision, LocationFormatter]

    def __init__(self, all_patches: dict[int, GamePatches], players_config: PlayersConfiguration):
        patches = all_patches[players_config.player_index]

        self.location_formatters = {
            HintLocationPrecision.DETAILED: TemplatedFormatter(
                "{determiner.title}{pickup} can be found in {node}.",
                self,
            ),
            HintLocationPrecision.WORLD_ONLY: TemplatedFormatter(
                "{determiner.title}{pickup} can be found in {node}.",
                self,
            ),
            HintLocationPrecision.RELATIVE_TO_AREA: RelativeAreaFormatter(
                patches, lambda msg, with_color: colorize_text(self.color_location, msg, with_color),
            ),
            HintLocationPrecision.RELATIVE_TO_INDEX: RelativeItemFormatter(
                patches, lambda msg, with_color: colorize_text(self.color_location, msg, with_color), players_config,
            ),
        }

    def format_joke(self, joke: str, with_color: bool) -> str:
        return colorize_text(self.color_joke, joke, with_color)

    def format_player(self, name: str, with_color: bool) -> str:
        return colorize_text(self.color_player, name, with_color)

    def format_world(self, location: PickupLocation, with_color: bool) -> str:
        world_list = default_database.game_description_for(location.game).world_list
        result = world_list.world_name_from_node(world_list.node_from_pickup_index(location.location), True)
        return colorize_text(self.color_location, result, with_color)

    def format_area(self, location: PickupLocation, with_world: bool, with_color: bool) -> str:
        world_list = default_database.game_description_for(location.game).world_list
        result = _area_name(world_list, world_list.node_from_pickup_index(location.location), not with_world)
        return colorize_text(self.color_location, result, with_color)

    def format_location_hint(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        return self.location_formatters[hint.precision.location].format(
            game,
            dataclasses.replace(
                pick_hint,
                pickup_name=colorize_text(self.color_item, pick_hint.pickup_name, with_color)
            ),
            hint,
            with_color,
        )

    def format_resource_is_starting(self, resource: ItemResourceInfo, with_color: bool) -> str:
        """Used when for when an item has a guaranteed hint, but is a starting item."""
        return "{} has no need to be located.".format(
            colorize_text(self.color_item, resource.long_name, with_color)
        )

    def format_guaranteed_resource(self, resource: ItemResourceInfo, player_name: Optional[str],
                                   location: PickupLocation, hide_area: bool, with_color: bool) -> str:
        determiner = ""
        if player_name is not None:
            determiner = self.format_player(player_name, with_color=with_color) + "'s "

        return "{} is located in {}{}.".format(
            colorize_text(self.color_item, resource.long_name, with_color),
            determiner,
            self.format_location(location, with_world=True, with_area=not hide_area, with_color=with_color),
        )

    def format_temple_name(self, temple_name: str, with_color: bool) -> str:
        raise NotImplementedError()

    @property
    def color_joke(self) -> str:
        raise NotImplementedError()

    @property
    def color_item(self) -> str:
        raise NotImplementedError()

    @property
    def color_player(self) -> str:
        raise NotImplementedError()

    @property
    def color_location(self) -> str:
        raise NotImplementedError()
