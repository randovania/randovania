import typing

from randovania.game_description import node_search
from randovania.game_description.world.area import Area
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintLocationPrecision, RelativeDataArea, HintRelativeAreaName
from randovania.game_description.world.node import PickupNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.world_list import WorldList
from randovania.games.prime.patcher_file_lib import hint_lib


class LocationFormatter:
    def format(self, determiner: hint_lib.Determiner, pickup_name: str, hint: Hint) -> str:
        raise NotImplementedError()


class GuardianFormatter(LocationFormatter):
    _GUARDIAN_NAMES = {
        PickupIndex(43): "Amorbis",
        PickupIndex(79): "Chykka",
        PickupIndex(115): "Quadraxis",
    }

    def format(self, determiner: hint_lib.Determiner, pickup: str, hint: Hint) -> str:
        guardian = hint_lib.color_text(hint_lib.TextColor.GUARDIAN, self._GUARDIAN_NAMES[hint.target])
        return f"{guardian} is guarding {determiner}{pickup}."


class TemplatedFormatter(LocationFormatter):
    def __init__(self, template: str, area_namer: hint_lib.AreaNamer):
        self.template = template
        self.hint_name_creator = area_namer

    def format(self, determiner: hint_lib.Determiner, pickup: str, hint: Hint) -> str:
        node_name = self.hint_name_creator.location_name(
            hint.target,
            hint.precision.location == HintLocationPrecision.WORLD_ONLY
        )
        return self.template.format(determiner=determiner,
                                    pickup=pickup,
                                    node=node_name)


class RelativeFormatter(LocationFormatter):
    def __init__(self, world_list: WorldList, patches: GamePatches):
        self.world_list = world_list
        self.patches = patches
        self._index_to_node = {
            node.pickup_index: node
            for node in world_list.all_nodes
            if isinstance(node, PickupNode)
        }

    def _calculate_distance(self, source_location: PickupIndex, target: Area) -> int:
        source = self._index_to_node[source_location]
        return node_search.distances_to_node(self.world_list, source,
                                             patches=self.patches, ignore_elevators=False)[target]

    def relative_format(self, determiner: hint_lib.Determiner, pickup: str, hint: Hint, other_area: Area, other_name: str,
                        ) -> str:
        distance = self._calculate_distance(hint.target, other_area) + (hint.precision.relative.distance_offset or 0)
        if distance == 1:
            distance_msg = "one room"
        else:
            precise_msg = "exactly " if hint.precision.relative.distance_offset is None else "up to "
            distance_msg = f"{precise_msg}{distance} rooms"

        return (f"{determiner.title}{pickup} can be found "
                f"{hint_lib.color_text(hint_lib.TextColor.LOCATION, distance_msg)} away from {other_name}.")

    def format(self, determiner: hint_lib.Determiner, pickup_name: str, hint: Hint) -> str:
        raise NotImplementedError()


class RelativeAreaFormatter(RelativeFormatter):
    def format(self, determiner: hint_lib.Determiner, pickup: str, hint: Hint) -> str:
        relative = typing.cast(RelativeDataArea, hint.precision.relative)
        other_area = self.world_list.area_by_area_location(relative.area_location)

        if relative.precision == HintRelativeAreaName.NAME:
            other_name = self.world_list.area_name(other_area)
        elif relative.precision == HintRelativeAreaName.FEATURE:
            raise NotImplementedError("HintRelativeAreaName.FEATURE not implemented")
        else:
            raise ValueError(f"Unknown precision: {relative.precision}")

        return self.relative_format(determiner, pickup, hint, other_area, other_name)
