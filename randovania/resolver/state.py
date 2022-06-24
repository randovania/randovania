import dataclasses
from typing import Optional, Iterator

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.logbook_node import LogbookNode
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.resource_node import ResourceNode
from randovania.game_description.world.world_list import WorldList


def _energy_tank_difference(new_resources: ResourceCollection,
                            old_resources: ResourceCollection,
                            database: ResourceDatabase,
                            ) -> int:
    return new_resources[database.energy_tank] - old_resources[database.energy_tank]


@dataclasses.dataclass(frozen=True)
class StateGameData:
    resource_database: ResourceDatabase
    world_list: WorldList
    energy_per_tank: int
    starting_energy: int


class State:
    resources: ResourceCollection
    collected_resource_nodes: tuple[ResourceNode, ...]
    energy: int
    node: Node
    patches: GamePatches
    previous_state: Optional["State"]
    path_from_previous_state: tuple[Node, ...]
    game_data: StateGameData

    @property
    def resource_database(self) -> ResourceDatabase:
        return self.game_data.resource_database

    @property
    def world_list(self) -> WorldList:
        return self.game_data.world_list

    def __init__(self,
                 resources: ResourceCollection,
                 collected_resource_nodes: tuple[ResourceNode, ...],
                 energy: int | None,
                 node: Node,
                 patches: GamePatches,
                 previous: Optional["State"],
                 game_data: StateGameData):

        self.resources = resources
        self.collected_resource_nodes = collected_resource_nodes
        self.node = node
        self.patches = patches
        self.path_from_previous_state = ()
        self.previous_state = previous
        self.game_data = game_data

        # We place this last because we need resource_database set
        if energy is None:
            energy = self.maximum_energy
        self.energy = min(energy, self.maximum_energy)

    def copy(self) -> "State":
        return State(self.resources.duplicate(),
                     self.collected_resource_nodes,
                     self.energy,
                     self.node,
                     self.patches,
                     self.previous_state,
                     self.game_data)

    @property
    def collected_pickup_indices(self) -> Iterator[PickupIndex]:
        for resource, count in self.resources.as_resource_gain():
            if count > 0 and isinstance(resource, NodeResourceInfo):
                node = self.world_list.node_by_identifier(resource.node_identifier)
                if isinstance(node, PickupNode):
                    yield node.pickup_index

    @property
    def collected_hints(self) -> Iterator[NodeIdentifier]:
        for resource, count in self.resources.as_resource_gain():
            if isinstance(resource, NodeIdentifier) and count > 0:
                if isinstance(self.world_list.node_by_identifier(resource), LogbookNode):
                    yield resource

    @property
    def collected_events(self) -> Iterator[ResourceInfo]:
        for resource, count in self.resources.as_resource_gain():
            if resource.resource_type == ResourceType.EVENT and count > 0:
                yield resource

    def take_damage(self, damage: int) -> "State":
        return State(self.resources, self.collected_resource_nodes, self.energy - damage, self.node, self.patches, self,
                     self.game_data)

    def heal(self) -> "State":
        return State(self.resources, self.collected_resource_nodes, self.maximum_energy, self.node, self.patches, self,
                     self.game_data)

    def _energy_for(self, resources: ResourceCollection) -> int:
        num_tanks = resources[self.game_data.resource_database.energy_tank]
        energy_per_tank = self.game_data.energy_per_tank
        return self.game_data.starting_energy + (energy_per_tank * num_tanks)

    @property
    def maximum_energy(self) -> int:
        return self._energy_for(self.resources)

    def collect_resource_node(self, node: ResourceNode, new_energy: int) -> "State":
        """
        Creates a new State that has the given ResourceNode collected.
        :param node:
        :param new_energy: How much energy you should have when collecting this resource
        :return:
        """

        if not node.can_collect(self.node_context()):
            raise ValueError(
                f"Trying to collect an uncollectable node'{node}'")

        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(node.resource_gain_on_collect(self.node_context()))

        energy = new_energy
        if _energy_tank_difference(new_resources, self.resources, self.resource_database) > 0:
            energy = self._energy_for(new_resources)

        return State(new_resources, self.collected_resource_nodes + (node,), energy, self.node, self.patches, self,
                     self.game_data)

    def act_on_node(self, node: ResourceNode, path: tuple[Node, ...] = (), new_energy: int | None = None) -> "State":
        if new_energy is None:
            new_energy = self.energy
        new_state = self.collect_resource_node(node, new_energy)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    def assign_pickup_resources(self, pickup: PickupEntry) -> "State":
        return self.assign_pickups_resources([pickup])

    def assign_pickups_resources(self, pickups: Iterator[PickupEntry]) -> "State":
        new_resources = self.resources.duplicate()
        for pickup in pickups:
            new_resources.add_resource_gain(pickup.resource_gain(self.resources, force_lock=True))

        energy = self.energy
        if _energy_tank_difference(new_resources, self.resources, self.resource_database) > 0:
            energy = self._energy_for(new_resources)

        return State(
            new_resources,
            self.collected_resource_nodes,
            energy,
            self.node,
            self.patches,
            self,
            self.game_data,
        )

    def assign_pickup_to_starting_items(self, pickup: PickupEntry) -> "State":
        pickup_resources = ResourceCollection.from_resource_gain(
            self.resource_database,
            pickup.resource_gain(self.resources, force_lock=True)
        )

        # Make sure there's no item percentage on starting items
        if self.resource_database.item_percentage is not None:
            pickup_resources.remove_resource(self.resource_database.item_percentage)

        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(pickup_resources.as_resource_gain())
        new_patches = self.patches.assign_extra_initial_items(pickup_resources.as_resource_gain())

        tank_delta = _energy_tank_difference(new_resources, self.resources, self.resource_database)

        return State(
            new_resources,
            self.collected_resource_nodes,
            self.energy + tank_delta * self.game_data.energy_per_tank,
            self.node,
            new_patches,
            self,
            self.game_data,
        )

    def node_context(self) -> NodeContext:
        return NodeContext(
            self.patches,
            self.resources,
            self.resource_database,
            self.game_data.world_list,
        )


def add_pickup_to_state(state: State, pickup: PickupEntry):
    """
    Modifies inplace the given state, adding the resources of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    state.resources.add_resource_gain(pickup.resource_gain(state.resources, force_lock=True))


def state_with_pickup(state: State,
                      pickup: PickupEntry,
                      ) -> State:
    """
    Returns a new State that follows the given State and also has the resource gain of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    new_state = state.copy()
    new_state.previous_state = state
    add_pickup_to_state(new_state, pickup)
    if new_state.maximum_energy > state.maximum_energy:
        new_state.energy = new_state.maximum_energy
    return new_state
