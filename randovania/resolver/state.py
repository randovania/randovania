import copy
from typing import Optional, Tuple, Iterator

from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.resources import ResourceInfo, CurrentResources, ResourceDatabase, PickupIndex, \
    ResourceGain, PickupEntry
from randovania.resolver.game_patches import GamePatches


class State:
    resources: CurrentResources
    node: Node
    previous_state: Optional["State"]
    path_from_previous_state: Tuple[Node, ...]
    resource_database: ResourceDatabase

    def __init__(self,
                 resources: CurrentResources,
                 node: Node,
                 previous: Optional["State"],
                 resource_database: ResourceDatabase):
        self.resources = resources
        self.node = node
        self.path_from_previous_state = ()
        self.previous_state = previous
        self.resource_database = resource_database

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.resources.get(resource, 0) > 0

    def copy(self) -> "State":
        return State(copy.copy(self.resources),
                     self.node,
                     self.previous_state,
                     self.resource_database)

    @property
    def collected_pickup_indices(self) -> Iterator[PickupIndex]:
        for resource, count in self.resources.items():
            if isinstance(resource, PickupIndex) and count > 0:
                yield resource

    def collect_resource_node(self, node: ResourceNode,
                              patches: GamePatches,
                              ) -> "State":

        resource = node.resource()
        if self.has_resource(resource):
            raise ValueError(
                "Trying to collect an already collected resource '{}'".format(
                    resource))

        new_resources = copy.copy(self.resources)
        for pickup_resource, quantity in node.resource_gain_on_collect(patches):
            new_resources[pickup_resource] = new_resources.get(pickup_resource, 0)
            new_resources[pickup_resource] += quantity

        return State(new_resources, self.node, self, self.resource_database)

    def act_on_node(self,
                    node: ResourceNode,
                    patches: GamePatches,
                    path: Tuple[Node, ...] = (),
                    ) -> "State":
        new_state = self.collect_resource_node(node, patches)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state


def add_resource_gain_to_state(state: State, resource_gain: ResourceGain):
    """
    Modifies inplace the given state, adding the given ResourceGain
    :param state:
    :param resource_gain:
    :return:
    """
    for resource, quantity in resource_gain:
        state.resources[resource] = state.resources.get(resource, 0)
        state.resources[resource] += quantity


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
    add_resource_gain_to_state(new_state, pickup.resource_gain())
    return new_state
