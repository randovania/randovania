from __future__ import annotations

import copy
import dataclasses
import typing
from dataclasses import dataclass
from typing import Tuple, Iterator, Optional

from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier

ElevatorConnection = dict[NodeIdentifier, Optional[AreaIdentifier]]

if typing.TYPE_CHECKING:
    from randovania.game_description.assignment import PickupAssignment, NodeConfigurationAssignment, PickupTarget
    from randovania.game_description.hint import Hint
    from randovania.game_description.requirements import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import CurrentResources
    from randovania.game_description.world.dock import DockWeakness
    from randovania.layout.base.base_configuration import BaseConfiguration


@dataclass(frozen=True)
class GamePatches:
    """Determines patches that are made to the game's data.
    Currently we support:
    * Swapping pickup locations
    """
    player_index: int
    configuration: BaseConfiguration
    pickup_assignment: PickupAssignment
    elevator_connection: ElevatorConnection
    dock_connection: dict[NodeIdentifier, Optional[NodeIdentifier]]
    dock_weakness: dict[NodeIdentifier, DockWeakness]
    configurable_nodes: dict[NodeIdentifier, Requirement]
    starting_items: CurrentResources
    starting_location: AreaIdentifier
    hints: dict[NodeIdentifier, Hint]

    def assign_new_pickups(self, assignments: Iterator[tuple[PickupIndex, PickupTarget]]) -> "GamePatches":
        new_pickup_assignment = copy.copy(self.pickup_assignment)

        for index, pickup in assignments:
            assert index not in new_pickup_assignment
            new_pickup_assignment[index] = pickup

        return dataclasses.replace(self, pickup_assignment=new_pickup_assignment)

    def assign_pickup_assignment(self, assignment: PickupAssignment) -> "GamePatches":
        items: Iterator[tuple[PickupIndex, PickupTarget]] = assignment.items()
        return self.assign_new_pickups(items)

    def assign_node_configuration(self, assignment: NodeConfigurationAssignment) -> "GamePatches":
        new_configurable = copy.copy(self.configurable_nodes)

        for identifier, requirement in assignment.items():
            assert identifier not in new_configurable
            new_configurable[identifier] = requirement

        return dataclasses.replace(self, configurable_nodes=new_configurable)

    def assign_starting_location(self, location: AreaIdentifier) -> "GamePatches":
        return dataclasses.replace(self, starting_location=location)

    def assign_extra_initial_items(self, new_resources: CurrentResources) -> "GamePatches":
        current = copy.copy(self.starting_items)

        for resource, quantity in new_resources.items():
            if resource.resource_type != ResourceType.ITEM:
                raise ValueError("Only ITEM is supported as extra initial items, got {}".format(resource.resource_type))
            current[resource] = current.get(resource, 0) + quantity

        return dataclasses.replace(self, starting_items=current)

    def assign_hint(self, identifier: NodeIdentifier, hint: Hint) -> "GamePatches":
        current = copy.copy(self.hints)
        current[identifier] = hint
        return dataclasses.replace(self, hints=current)

    def get_pickup_index_from_name(self, name: str) -> PickupIndex:
        for pickup_index in self.pickup_assignment:
            if self.pickup_assignment[pickup_index].pickup.name == name:
                return pickup_index
        raise Exception("Failed to find pickup " + name)
