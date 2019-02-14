import copy
from typing import Optional, Tuple, Iterator

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.resources import ResourceInfo, CurrentResources, ResourceDatabase, PickupIndex, \
    ResourceGain, PickupEntry


class State:
    resources: CurrentResources
    node: Node
    patches: GamePatches
    previous_state: Optional["State"]
    path_from_previous_state: Tuple[Node, ...]
    resource_database: ResourceDatabase

    def __init__(self,
                 resources: CurrentResources,
                 node: Node,
                 patches: GamePatches,
                 previous: Optional["State"],
                 resource_database: ResourceDatabase):
        self.resources = resources
        self.node = node
        self.patches = patches
        self.path_from_previous_state = ()
        self.previous_state = previous
        self.resource_database = resource_database

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.resources.get(resource, 0) > 0

    def copy(self) -> "State":
        return State(copy.copy(self.resources),
                     self.node,
                     self.patches,
                     self.previous_state,
                     self.resource_database)

    @property
    def collected_pickup_indices(self) -> Iterator[PickupIndex]:
        for resource, count in self.resources.items():
            if isinstance(resource, PickupIndex) and count > 0:
                yield resource

    def collect_resource_node(self, node: ResourceNode) -> "State":

        resource = node.resource()
        if self.has_resource(resource):
            raise ValueError(
                "Trying to collect an already collected resource '{}'".format(
                    resource))

        new_resources = copy.copy(self.resources)
        add_resource_gain_to_current_resources(node.resource_gain_on_collect(self.patches, self.resources),
                                               new_resources)

        return State(new_resources, self.node, self.patches, self, self.resource_database)

    def act_on_node(self, node: ResourceNode, path: Tuple[Node, ...] = ()) -> "State":
        new_state = self.collect_resource_node(node)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    def assign_pickup_to_index(self, index: PickupIndex, pickup: PickupEntry) -> "State":
        new_patches = self.patches.assign_new_pickups([(index, pickup)])
        new_resources = copy.copy(self.resources)

        if index in self.resources:
            add_resource_gain_to_current_resources(pickup.resource_gain(self.resources), new_resources)

        return State(
            new_resources,
            self.node,
            new_patches,
            self,
            self.resource_database
        )


def add_resource_gain_to_current_resources(resource_gain: ResourceGain, resources: CurrentResources):
    """
    Adds all resources from the given gain to the given CurrentResources
    :param resource_gain:
    :param resources:
    :return:
    """
    for resource, quantity in resource_gain:
        resources[resource] = resources.get(resource, 0)
        resources[resource] += quantity


def add_pickup_to_state(state: State, pickup: PickupEntry):
    """
    Modifies inplace the given state, adding the resources of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    add_resource_gain_to_current_resources(pickup.resource_gain(state.resources), state.resources)


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
    return new_state
