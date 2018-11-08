import collections
import json
from distutils.version import StrictVersion
from typing import NamedTuple, Tuple, Dict, Optional, List

import randovania.games.prime.claris_randomizer
from randovania.game_description import echoes_elevator, data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import PickupNode
from randovania.games.prime import binary_data
from randovania.resolver.game_patches import PickupAssignment
from randovania.resolver.layout_configuration import LayoutConfiguration


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


def _pickup_assignment_to_item_locations(game: GameDescription,
                                         pickup_assignment: PickupAssignment,
                                         ) -> Dict[str, Dict[str, str]]:
    items_locations = {}

    for world in game.worlds:
        items_in_world = {}
        items_locations[world.name] = items_in_world

        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, PickupNode):
                    if node.pickup_index in pickup_assignment:
                        item_name = pickup_assignment[node.pickup_index].item
                    else:
                        item_name = "Nothing"
                    items_in_world[game.node_name(node)] = item_name

    return items_locations


def _elevator_to_location(game: GameDescription,
                          elevator: echoes_elevator.Elevator,
                          ) -> str:
    world = game.world_by_asset_id(elevator.world_asset_id)
    return "{}/{}".format(
        world.name,
        world.area_by_asset_id(elevator.area_asset_id).name
    )


def _playthrough_list_to_solver_path(playthrough: List[dict]) -> Tuple[SolverPath, ...]:
    return tuple(
        SolverPath(
            node_name=step["node"],
            previous_nodes=tuple(step["path_from_previous"])
        )
        for step in playthrough
    )


def _item_locations_to_pickup_assignment(locations: Dict[str, Dict[str, str]]) -> PickupAssignment:
    game = data_reader.decode_data(binary_data.decode_default_prime2(), [])
    pickup_assignment = {}

    pickup_by_name = {
        pickup.name: pickup
        for pickup in game.pickup_database.pickups
    }

    for world_name, world_data in locations.items():
        world = [world for world in game.worlds if world.name == world_name][0]
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

            pickup_assignment[node.pickup_index] = pickup_by_name[name]

    return pickup_assignment


class LayoutDescription(NamedTuple):
    version: str
    configuration: LayoutConfiguration
    seed_number: int
    pickup_assignment: PickupAssignment
    solver_path: Tuple[SolverPath, ...]

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "LayoutDescription":
        version = json_dict["info"]["version"]
        if StrictVersion(version) < StrictVersion("0.12.0"):
            seed = json_dict["info"]["configuration"]["seed"]
        else:
            seed = json_dict["info"]["seed"]

        # TODO: add try/catch to throw convert potential errors in "seed from future version broke"

        return LayoutDescription(
            version=version,
            configuration=LayoutConfiguration.from_json_dict(json_dict["info"]["configuration"]),
            seed_number=seed,
            pickup_assignment=_item_locations_to_pickup_assignment(json_dict["locations"]),
            solver_path=_playthrough_list_to_solver_path(json_dict["playthrough"]),
        )

    @classmethod
    def from_file(cls, json_path: str) -> "LayoutDescription":
        with open(json_path, "r") as open_file:
            return cls.from_json_dict(json.load(open_file))

    @property
    def as_json(self) -> dict:
        game = data_reader.decode_data(binary_data.decode_default_prime2(), [])
        return {
            "info": {
                "version": self.version,
                "seed": self.seed_number,
                "configuration": self.configuration.as_json,
            },
            "locations": {
                key: value
                for key, value in sorted(_pickup_assignment_to_item_locations(game, self.pickup_assignment).items())
            },
            "elevators": {
                _elevator_to_location(game, elevator): _elevator_to_location(game, elevator.connected_elevator)
                for elevator in
                randovania.games.prime.claris_randomizer.elevator_list_for_configuration(self.configuration,
                                                                                         self.seed_number)
            },
            "playthrough": [
                {
                    "path_from_previous": path.previous_nodes,
                    "node": path.node_name,
                }
                for path in self.solver_path
            ]
        }

    def save_to_file(self, json_path: str):
        with open(json_path, "w") as open_file:
            json.dump(self.as_json, open_file, indent=4, separators=(',', ': '))

    @property
    def without_solver_path(self) -> "LayoutDescription":
        """
        A solver path is way too big to reasonably store for test purposes, so use LayoutDescriptions with an empty one.
        :return:
        """
        return LayoutDescription(
            seed_number=self.seed_number,
            configuration=self.configuration,
            version=self.version,
            pickup_assignment=self.pickup_assignment,
            solver_path=())
