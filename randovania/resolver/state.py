import copy
import dataclasses
from typing import Optional, Tuple, Iterator

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.node import ResourceNode, Node
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources, \
    add_resource_gain_to_current_resources, add_resources_into_another, convert_resource_gain_to_current_resources
from randovania.game_description.world.world_list import WorldList


def _energy_tank_difference(new_resources: CurrentResources,
                            old_resources: CurrentResources,
                            database: ResourceDatabase,
                            ) -> int:
    return new_resources.get(database.energy_tank, 0) - old_resources.get(database.energy_tank, 0)


@dataclasses.dataclass(frozen=True)
class StateGameData:
    resource_database: ResourceDatabase
    world_list: WorldList
    energy_per_tank: int


class State:
    resources: CurrentResources
    collected_resource_nodes: Tuple[ResourceNode, ...]
    energy: int
    node: Node
    patches: GamePatches
    previous_state: Optional["State"]
    path_from_previous_state: Tuple[Node, ...]
    game_data: StateGameData

    @property
    def resource_database(self) -> ResourceDatabase:
        return self.game_data.resource_database

    @property
    def world_list(self) -> WorldList:
        return self.game_data.world_list

    def __init__(self,
                 resources: CurrentResources,
                 collected_resource_nodes: Tuple[ResourceNode, ...],
                 energy: int,
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
        self.energy = min(energy, self.maximum_energy)

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.resources.get(resource, 0) > 0

    def copy(self) -> "State":
        return State(copy.copy(self.resources),
                     self.collected_resource_nodes,
                     self.energy,
                     self.node,
                     self.patches,
                     self.previous_state,
                     self.game_data)

    @property
    def collected_pickup_indices(self) -> Iterator[PickupIndex]:
        for resource, count in self.resources.items():
            if isinstance(resource, PickupIndex) and count > 0:
                yield resource

    @property
    def collected_scan_assets(self) -> Iterator[LogbookAsset]:
        for resource, count in self.resources.items():
            if isinstance(resource, LogbookAsset) and count > 0:
                yield resource

    @property
    def collected_events(self) -> Iterator[ResourceInfo]:
        for resource, count in self.resources.items():
            if resource.resource_type == ResourceType.EVENT and count > 0:
                yield resource

    def take_damage(self, damage: int) -> "State":
        return State(self.resources, self.collected_resource_nodes, self.energy - damage, self.node, self.patches, self,
                     self.game_data)

    def heal(self) -> "State":
        return State(self.resources, self.collected_resource_nodes, self.maximum_energy, self.node, self.patches, self,
                     self.game_data)

    def _energy_for(self, resources: CurrentResources) -> int:
        num_tanks = resources.get(self.game_data.resource_database.energy_tank, 0)
        energy_per_tank = self.game_data.energy_per_tank
        return (energy_per_tank - 1) + (energy_per_tank * num_tanks)

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

        if not node.can_collect(self.patches, self.resources, self.world_list.all_nodes, self.resource_database):
            raise ValueError(
                "Trying to collect an uncollectable node'{}'".format(node))

        new_resources = copy.copy(self.resources)
        add_resource_gain_to_current_resources(node.resource_gain_on_collect(self.patches, self.resources,
                                                                             self.world_list.all_nodes,
                                                                             self.resource_database),
                                               new_resources)

        energy = new_energy
        if _energy_tank_difference(new_resources, self.resources, self.resource_database) > 0:
            energy = self._energy_for(new_resources)

        return State(new_resources, self.collected_resource_nodes + (node,), energy, self.node, self.patches, self,
                     self.game_data)

    def act_on_node(self, node: ResourceNode, path: Tuple[Node, ...] = (), new_energy: Optional[int] = None) -> "State":
        if new_energy is None:
            new_energy = self.energy
        new_state = self.collect_resource_node(node, new_energy)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    def assign_pickup_resources(self, pickup: PickupEntry) -> "State":
        return self.assign_pickups_resources([pickup])

    def assign_pickups_resources(self, pickups: Iterator[PickupEntry]) -> "State":
        new_resources = copy.copy(self.resources)
        for pickup in pickups:
            add_resource_gain_to_current_resources(pickup.resource_gain(self.resources, force_lock=True), new_resources)

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
        pickup_resources = convert_resource_gain_to_current_resources(
            pickup.resource_gain(self.resources, force_lock=True))

        # Make sure there's no item percentage on starting items
        if self.resource_database.item_percentage is not None:
            pickup_resources.pop(self.resource_database.item_percentage, None)

        new_resources = copy.copy(self.resources)
        add_resources_into_another(new_resources, pickup_resources)
        new_patches = self.patches.assign_extra_initial_items(pickup_resources)

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


def add_pickup_to_state(state: State, pickup: PickupEntry):
    """
    Modifies inplace the given state, adding the resources of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    add_resource_gain_to_current_resources(pickup.resource_gain(state.resources, force_lock=True), state.resources)


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
