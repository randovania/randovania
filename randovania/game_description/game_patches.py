import copy
import dataclasses
from dataclasses import dataclass
from typing import Dict, Tuple, Iterator, Optional

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.assignment import PickupAssignment, GateAssignment, PickupTarget
from randovania.game_description.world.dock import DockWeakness, DockConnection
from randovania.game_description.hint import Hint
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.teleporter import Teleporter


ElevatorConnection = Dict[Teleporter, Optional[AreaLocation]]


@dataclass(frozen=True)
class GamePatches:
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """
    player_index: int
    pickup_assignment: PickupAssignment
    elevator_connection: ElevatorConnection
    dock_connection: Dict[Tuple[int, int], Optional[DockConnection]]
    dock_weakness: Dict[Tuple[int, int], DockWeakness]
    translator_gates: GateAssignment
    starting_items: CurrentResources
    starting_location: AreaLocation
    hints: Dict[LogbookAsset, Hint]

    def assign_new_pickups(self, assignments: Iterator[Tuple[PickupIndex, PickupTarget]]) -> "GamePatches":
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return dataclasses.replace(self, pickup_assignment=new_pickup_assignment)

    def assign_pickup_assignment(self, assignment: PickupAssignment) -> "GamePatches":
        items: Iterator[Tuple[PickupIndex, PickupTarget]] = assignment.items()
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
