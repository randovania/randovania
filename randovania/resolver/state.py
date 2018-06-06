import copy
from typing import Optional

from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import Logic
from randovania.resolver.node import ResourceNode, Node
from randovania.resolver.resources import ResourceInfo, CurrentResources, ResourceGain, ResourceType, ResourceDatabase


class State:
    resources: CurrentResources
    node: Node
    previous_state: Optional["State"]
    logic: Logic

    @property
    def game(self) -> GameDescription:
        return self.logic.game

    def __init__(self,
                 resources: CurrentResources,
                 node: Node,
                 previous: Optional["State"],
                 logic: Logic):
        self.resources = resources
        self.node = node
        self.previous_state = previous
        self.logic = logic

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.resources.get(resource, 0) > 0

    def collect_resource_node(self, node: ResourceNode,
                              resource_database: ResourceDatabase,
                              game_patches: GamePatches) -> "State":

        resource = node.resource(resource_database)
        if self.has_resource(resource):
            raise ValueError(
                "Trying to collect an already collected resource '{}'".format(
                    resource))

        new_resources = copy.copy(self.resources)
        for pickup_resource, quantity in node.resource_gain_on_collect(resource_database, game_patches):
            new_resources[pickup_resource] = new_resources.get(pickup_resource, 0)
            new_resources[pickup_resource] += quantity

        return State(new_resources, self.node, self, self.logic)

    def act_on_node(self,
                    node: ResourceNode,
                    resource_database: ResourceDatabase,
                    game_patches: GamePatches) -> "State":
        new_state = self.collect_resource_node(node, resource_database, game_patches)
        new_state.node = node
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
            logic
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
            for event_id in (71, 78, 2, 4):
                resource = game.resource_database.get_by_type_and_index(ResourceType.EVENT, event_id)
                starting_state.resources[resource] = 1
        else:
            add_resources_from(game.item_loss_items)

        return starting_state
