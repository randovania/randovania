from typing import Callable

from randovania.exporter.hints.determiner import Determiner
from randovania.exporter.hints.hint_namer import HintNamer, PickupLocation
from randovania.exporter.hints.pickup_hint import PickupHint
from randovania.game_description import node_search
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintLocationPrecision, RelativeDataArea, HintRelativeAreaName
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.area import Area
from randovania.games.game import RandovaniaGame
from randovania.layout import filtered_database


class LocationFormatter:
    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        raise NotImplementedError()


class TemplatedFormatter(LocationFormatter):
    def __init__(self, template: str, namer: HintNamer, with_world: bool = True, upper_pickup: bool = False):
        self.template = template
        self.namer = namer
        self.with_world = with_world
        self.upper_pickup = upper_pickup

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        node_name = self.namer.format_location(
            location=PickupLocation(game, hint.target),
            with_world=self.with_world or hint.precision.location == HintLocationPrecision.WORLD_ONLY,
            with_area=hint.precision.location != HintLocationPrecision.WORLD_ONLY,
            with_color=with_color,
        )
        pickup = pick_hint.pickup_name
        if self.upper_pickup:
            pickup = pickup.upper()

        if pick_hint.player_name is not None:
            name = self.namer.format_player(pick_hint.player_name, with_color=with_color)
            determiner = Determiner(f"{name}'s ", supports_title=False)
        else:
            determiner = pick_hint.determiner

        return self.template.format(
            determiner=determiner,
            pickup=pickup,
            node=node_name,
        )


class RelativeFormatter(LocationFormatter):
    def __init__(self, patches: GamePatches, distance_painter: Callable[[str, bool], str]):
        self.world_list = filtered_database.game_description_for_layout(patches.configuration).world_list
        self.patches = patches
        self.distance_painter = distance_painter

    def _calculate_distance(self, source_location: PickupIndex, target: Area) -> int:
        source = self.world_list.node_from_pickup_index(source_location)
        return node_search.distances_to_node(self.world_list, source,
                                             patches=self.patches, ignore_elevators=False)[target]

    def relative_format(self, pick_hint: PickupHint,
                        hint: Hint,
                        other_area: Area,
                        other_name: str,
                        with_color: bool,
                        ) -> str:
        distance = self._calculate_distance(hint.target, other_area) + (hint.precision.relative.distance_offset or 0)
        if distance == 1:
            distance_msg = "one room"
        else:
            precise_msg = "exactly " if hint.precision.relative.distance_offset is None else "up to "
            distance_msg = f"{precise_msg}{distance} rooms"

        colored_dist = self.distance_painter(distance_msg, with_color)
        return (f"{pick_hint.determiner.title}{pick_hint.pickup_name}"
                f" can be found {colored_dist} away from {other_name}.")

    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        raise NotImplementedError()


class RelativeAreaFormatter(RelativeFormatter):
    def format(self, game: RandovaniaGame, pick_hint: PickupHint, hint: Hint, with_color: bool) -> str:
        relative = hint.precision.relative
        assert isinstance(relative, RelativeDataArea)
        other_area = self.world_list.area_by_area_location(relative.area_location)

        if relative.precision == HintRelativeAreaName.NAME:
            other_name = self.world_list.area_name(other_area)
        elif relative.precision == HintRelativeAreaName.FEATURE:
            raise NotImplementedError("HintRelativeAreaName.FEATURE not implemented")
        else:
            raise ValueError(f"Unknown precision: {relative.precision}")

        return self.relative_format(pick_hint, hint, other_area, other_name, with_color)
