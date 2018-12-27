import collections
import json
from dataclasses import dataclass
from distutils.version import StrictVersion
from pathlib import Path
from typing import NamedTuple, Tuple, Dict, List

from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import PickupNode, Node, TeleporterNode, TeleporterConnection
from randovania.game_description.resources import PickupAssignment
from randovania.game_description.world_list import WorldList
from randovania.resolver.permalink import Permalink


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


def _pickup_assignment_to_item_locations(world_list: WorldList,
                                         pickup_assignment: PickupAssignment,
                                         ) -> Dict[str, Dict[str, str]]:
    items_locations = {}

    for world in world_list.worlds:
        items_in_world = {}
        items_locations[world.name] = items_in_world

        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, PickupNode):
                    if node.pickup_index in pickup_assignment:
                        item_name = pickup_assignment[node.pickup_index].name
                    else:
                        item_name = "Nothing"
                    items_in_world[world_list.node_name(node)] = item_name

    return items_locations


def _playthrough_list_to_solver_path(playthrough: List[dict]) -> Tuple[SolverPath, ...]:
    return tuple(
        SolverPath(
            node_name=step["node"],
            previous_nodes=tuple(step["path_from_previous"])
        )
        for step in playthrough
    )


def _item_locations_to_pickup_assignment(game: GameDescription,
                                         locations: Dict[str, Dict[str, str]],
                                         ) -> PickupAssignment:
    pickup_assignment = {}

    for world_name, world_data in locations.items():
        world = [world for world in game.world_list.worlds if world.name == world_name][0]
        areas_by_name = collections.defaultdict(list)
        for area in world.areas:
            areas_by_name[area.name].append(area)

        for location_name, name in world_data.items():
            if name == "Nothing":
                continue

            area_name, node_name = location_name.split("/", maxsplit=1)
            node: PickupNode = None

            for area in areas_by_name[area_name]:
                nodes = [node for node in area.nodes if node.name == node_name]
                if len(nodes) == 1:
                    node = nodes[0]
                    break

            pickup_assignment[node.pickup_index] = game.pickup_database.pickup_by_name(name)

    return pickup_assignment


def _node_mapping_to_elevator_connection(world_list: WorldList,
                                         elevators: Dict[str, str],
                                         ) -> Dict[int, TeleporterConnection]:

    result = {}
    for source_name, target_node in elevators.items():
        source_node: TeleporterNode = world_list.node_from_name(source_name)
        target_node = world_list.node_from_name(target_node)

        result[source_node.teleporter_instance_id] = TeleporterConnection(
            world_list.nodes_to_world(target_node).world_asset_id,
            world_list.nodes_to_area(target_node).area_asset_id
        )

    return result


def _find_node_with_teleporter(world_list: WorldList, teleporter_id: int) -> Node:
    for node in world_list.all_nodes:
        if isinstance(node, TeleporterNode):
            if node.teleporter_instance_id == teleporter_id:
                return node
    raise ValueError("Unknown teleporter_id: {}".format(teleporter_id))


@dataclass(frozen=True)
class LayoutDescription:
    version: str
    permalink: Permalink
    patches: GamePatches
    solver_path: Tuple[SolverPath, ...]

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        version = json_dict["info"]["version"]
        version_as_obj = StrictVersion(version)

        if version_as_obj < StrictVersion("0.17.0"):
            raise RuntimeError("Unsupported log file version '{}'.".format(version))

        # TODO: add try/catch to throw convert potential errors in "seed from future version broke"
        permalink = Permalink.from_json_dict(json_dict["info"]["permalink"])

        if not permalink.spoiler:
            raise ValueError("Unable to read details of seed log with spoiler disabled")

        game = data_reader.decode_data(permalink.layout_configuration.game_data)
        patches = GamePatches(
            _item_locations_to_pickup_assignment(game, json_dict["locations"]),
            _node_mapping_to_elevator_connection(game.world_list, json_dict["elevators"]),
            {},
            {}
        )

        return LayoutDescription(
            version=version,
            permalink=permalink,
            patches=patches,
            solver_path=_playthrough_list_to_solver_path(json_dict["playthrough"]),
        )

    @classmethod
    def from_file(cls, json_path: Path) -> "LayoutDescription":
        with json_path.open("r") as open_file:
            return cls.from_json_dict(json.load(open_file))

    @property
    def as_json(self) -> dict:
        result = {
            "info": {
                "version": self.version,
                "permalink": self.permalink.as_json,
            }
        }

        if self.permalink.spoiler:
            world_list = data_reader.decode_data(self.permalink.layout_configuration.game_data).world_list

            result["locations"] = {
                key: value
                for key, value in sorted(_pickup_assignment_to_item_locations(world_list,
                                                                              self.patches.pickup_assignment).items())
            }
            result["elevators"] = {
                world_list.node_name(_find_node_with_teleporter(world_list, teleporter_id), with_world=True):
                    world_list.node_name(world_list.resolve_teleporter_connection(connection), with_world=True)
                for teleporter_id, connection in self.patches.elevator_connection.items()
            }
            result["playthrough"] = [
                {
                    "path_from_previous": path.previous_nodes,
                    "node": path.node_name,
                }
                for path in self.solver_path
            ]

        return result

    def save_to_file(self, json_path: Path):
        with json_path.open("w") as open_file:
            json.dump(self.as_json, open_file, indent=4, separators=(',', ': '))

    @property
    def without_solver_path(self) -> "LayoutDescription":
        """
        A solver path is way too big to reasonably store for test purposes, so use LayoutDescriptions with an empty one.
        :return:
        """
        return LayoutDescription(
            permalink=self.permalink,
            version=self.version,
            patches=self.patches,
            solver_path=())
