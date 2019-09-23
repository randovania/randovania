import copy
import dataclasses
from dataclasses import dataclass
from typing import Dict, Tuple, Iterator

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.assignment import PickupAssignment, GateAssignment
from randovania.game_description.dock import DockWeakness, DockConnection
from randovania.game_description.hint import Hint
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType


@dataclass(frozen=True)
class GamePatches:
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """

    pickup_assignment: PickupAssignment
    elevator_connection: Dict[int, AreaLocation]
    dock_connection: Dict[Tuple[int, int], DockConnection]
    dock_weakness: Dict[Tuple[int, int], DockWeakness]
    translator_gates: GateAssignment
    starting_items: CurrentResources
    starting_location: AreaLocation
    hints: Dict[LogbookAsset, Hint]

    @classmethod
    def with_game(cls, game: "GameDescription") -> "GamePatches":
        from randovania.game_description.node import TeleporterNode
        elevator_connection = {
            node.teleporter_instance_id: node.default_connection

            for node in game.world_list.all_nodes
            if isinstance(node, TeleporterNode) and node.editable
        }

        return GamePatches({}, elevator_connection, {}, {}, {}, {}, game.starting_location, {})

    def assign_new_pickups(self, assignments: Iterator[Tuple[PickupIndex, PickupEntry]]) -> "GamePatches":
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return dataclasses.replace(self, pickup_assignment=new_pickup_assignment)

    def assign_pickup_assignment(self, assignment: PickupAssignment) -> "GamePatches":
        items: Iterator[Tuple[PickupIndex, PickupEntry]] = assignment.items()
        return self.assign_new_pickups(items)

    def assign_gate_assignment(self, assignment: GateAssignment) -> "GamePatches":
        new_translator_gates = copy.copy(self.translator_gates)

        for gate, translator in assignment.items():
            assert gate not in new_translator_gates
            assert gate.resource_type == ResourceType.GATE_INDEX
            new_translator_gates[gate] = translator

        return dataclasses.replace(self, translator_gates=new_translator_gates)

    def assign_starting_location(self, location: AreaLocation) -> "GamePatches":
        return dataclasses.replace(self, starting_location=location)

    def assign_extra_initial_items(self, new_resources: CurrentResources) -> "GamePatches":
        current = copy.copy(self.starting_items)

        for resource, quantity in new_resources.items():
            if resource.resource_type != ResourceType.ITEM:
                raise ValueError("Only ITEM is supported as extra initial items, got {}".format(resource.resource_type))
            current[resource] = current.get(resource, 0) + quantity

        return dataclasses.replace(self, starting_items=current)

    def assign_hint(self, logbook: LogbookAsset, hint: Hint) -> "GamePatches":
        current = copy.copy(self.hints)
        current[logbook] = hint
        return dataclasses.replace(self, hints=current)
