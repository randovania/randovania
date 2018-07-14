import collections
import json
from typing import NamedTuple, Tuple, Dict, Optional

from randovania.games.prime import binary_data
from randovania.resolver import data_reader
from randovania.resolver.layout_configuration import LayoutConfiguration
from randovania.resolver.node import PickupNode


class SolverPath(NamedTuple):
    node_name: str
    previous_nodes: Tuple[str, ...]


def _pickup_mapping_to_item_locations(pickup_mapping: Tuple[int, ...]) -> Dict[str, Dict[str, str]]:
    game = data_reader.decode_data(binary_data.decode_default_prime2(), [])

    items_locations = {}

    for world in game.worlds:
        items_in_world = {}
        items_locations[world.name] = items_in_world

        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, PickupNode):
                    new_index = pickup_mapping[node.pickup_index.index]
                    if new_index is not None:
                        item_name = game.resource_database.pickups[new_index].item
                    else:
                        item_name = "Nothing"
                    items_in_world[game.node_name(node)] = item_name

    return items_locations


class LayoutDescription(NamedTuple):
    configuration: LayoutConfiguration
    version: str
    pickup_mapping: Tuple[Optional[int], ...]
    solver_path: Tuple[SolverPath, ...]

    @property
    def as_json(self) -> dict:
        return {
            "info": {
                "version": self.version,
                "configuration": self.configuration.as_json,
            },
            "locations": _pickup_mapping_to_item_locations(self.pickup_mapping),
            "playthrough": [
                {
                    "node": path.node_name,
                    "path_from_previous": path.previous_nodes
                }
                for path in self.solver_path
            ]
        }

    def save_to_file(self, json_path: str):
        with open(json_path, "w") as open_file:
            json.dump(self.as_json, open_file, sort_keys=True, indent=4, separators=(',', ': '))

    @property
    def without_solver_path(self) -> "LayoutDescription":
        """
        A solver path is way too big to reasonably store for test purposes, so use LayoutDescriptions with an empty one.
        :return:
        """
        return LayoutDescription(
            configuration=self.configuration,
            version=self.version,
            pickup_mapping=self.pickup_mapping,
            solver_path=())
