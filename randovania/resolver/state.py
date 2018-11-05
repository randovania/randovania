import copy
from typing import Optional, List, Tuple, Iterator

from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.resources import ResourceInfo, CurrentResources, ResourceGain, ResourceType, \
    ResourceDatabase, PickupIndex
from randovania.resolver.logic import Logic


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
                              pickup_mapping: List[Optional[int]]) -> "State":

        resource = node.resource()
        if self.has_resource(resource):
            raise ValueError(
                "Trying to collect an already collected resource '{}'".format(
                    resource))

        new_resources = copy.copy(self.resources)
        for pickup_resource, quantity in node.resource_gain_on_collect(self.resource_database, pickup_mapping):
            new_resources[pickup_resource] = new_resources.get(pickup_resource, 0)
            new_resources[pickup_resource] += quantity

        return State(new_resources, self.node, self, self.resource_database)

    def act_on_node(self,
                    node: ResourceNode,
                    pickup_mapping: List[Optional[int]],
                    path: Tuple[Node, ...] = (),
                    ) -> "State":
        new_state = self.collect_resource_node(node, pickup_mapping)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    @classmethod
    def calculate_starting_state(cls,
                                 logic: Logic) -> "State":
        game = logic.game

        starting_world = game.world_by_asset_id(game.starting_world_asset_id)
        starting_area = starting_world.area_by_asset_id(game.starting_area_asset_id)
        starting_node = starting_area.nodes[starting_area.default_node_index]

        starting_state = State(
            {
                # "No Requirements"
                game.resource_database.trivial_resource(): 1
            },
            starting_node,
            None,
            game.resource_database
        )

        def add_resources_from(resource_gain: ResourceGain):
            for pickup_resource, quantity in resource_gain:
                starting_state.resources[pickup_resource] = starting_state.resources.get(pickup_resource, 0)
                starting_state.resources[pickup_resource] += quantity

        add_resources_from(game.starting_items)
        if logic.patches.item_loss_enabled:
            # TODO: not hardcode this data here.
            # TODO: actually lose the items when trigger the Item Loss cutscene
            # These ids are all events you trigger before reaching the IL cutscene in echoes
            # We're giving these items right now because you need the items you lose to be able to get here.
            for event_id in (71, 78, 2, 4):
                resource = game.resource_database.get_by_type_and_index(ResourceType.EVENT, event_id)
                starting_state.resources[resource] = 1
        else:
            add_resources_from(game.item_loss_items)

        return starting_state
