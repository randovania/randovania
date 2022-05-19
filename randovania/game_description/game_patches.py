from __future__ import annotations

import copy
import dataclasses
import typing
from dataclasses import dataclass
from typing import Iterator, Optional

from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.resources.resource_info import ResourceCollection, ResourceGain

ElevatorConnection = dict[NodeIdentifier, Optional[AreaIdentifier]]

if typing.TYPE_CHECKING:
    from randovania.game_description.assignment import PickupAssignment, NodeConfigurationAssignment, PickupTarget
    from randovania.game_description.hint import Hint
    from randovania.game_description.requirements import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
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
    starting_items: ResourceCollection
    starting_location: AreaIdentifier
    hints: dict[NodeIdentifier, Hint]

    def __post_init__(self):
        from randovania.game_description.resources.resource_info import ResourceCollection
        if not isinstance(self.starting_items, ResourceCollection):
            raise TypeError("starting_items must be a ResourceCollection")

        for resource, _ in self.starting_items.as_resource_gain():
            if resource.resource_type != ResourceType.ITEM:
                raise ValueError(f"starting_items must have only Items, not {resource}")

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

    def assign_extra_initial_items(self, new_resources: ResourceGain) -> "GamePatches":
        current = self.starting_items.duplicate()
        current.add_resource_gain(new_resources)
        return dataclasses.replace(self, starting_items=current)

    def assign_hint(self, identifier: NodeIdentifier, hint: Hint) -> "GamePatches":
        current = copy.copy(self.hints)
        current[identifier] = hint
        return dataclasses.replace(self, hints=current)
