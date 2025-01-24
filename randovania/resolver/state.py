from __future__ import annotations

from typing import TYPE_CHECKING, Self

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.resolver.damage_state import DamageState


class State:
    resources: ResourceCollection
    collected_resource_nodes: tuple[ResourceNode, ...]
    damage_state: DamageState
    node: Node
    patches: GamePatches
    previous_state: Self | None
    path_from_previous_state: tuple[Node, ...]

    @property
    def resource_database(self) -> ResourceDatabase:
        return self.damage_state.resource_database()

    @property
    def region_list(self) -> RegionList:
        return self.damage_state.region_list()

    def __init__(
        self,
        resources: ResourceCollection,
        collected_resource_nodes: tuple[ResourceNode, ...],
        damage_state: DamageState,
        node: Node,
        patches: GamePatches,
        previous: Self | None,
    ):
        self.resources = resources
        self.collected_resource_nodes = collected_resource_nodes
        self.node = node
        self.patches = patches
        self.path_from_previous_state = ()
        self.previous_state = previous

        # We place this last because we need resource_database set
        self.damage_state = damage_state.limited_by_maximum(self.resources)

    def copy(self) -> Self:
        return State(
            self.resources.duplicate(),
            self.collected_resource_nodes,
            self.damage_state,
            self.node,
            self.patches,
            self.previous_state,
        )

    @property
    def collected_pickup_indices(self) -> Iterator[PickupIndex]:
        context = self.node_context()
        for resource, count in self.resources.as_resource_gain():
            if count > 0 and isinstance(resource, NodeResourceInfo):
                node = resource.to_node(context)
                if isinstance(node, PickupNode):
                    yield node.pickup_index

    @property
    def collected_hints(self) -> Iterator[NodeIdentifier]:
        context = self.node_context()
        for resource, count in self.resources.as_resource_gain():
            if isinstance(resource, NodeResourceInfo) and count > 0:
                if isinstance(resource.to_node(context), HintNode):
                    yield resource.node_identifier

    @property
    def collected_events(self) -> Iterator[ResourceInfo]:
        for resource, count in self.resources.as_resource_gain():
            if resource.resource_type == ResourceType.EVENT and count > 0:
                yield resource

    @property
    def health_for_damage_requirements(self) -> int:
        # TODO: keep the wrapper?
        return self.damage_state.health_for_damage_requirements()

    def game_state_debug_string(self) -> str:
        """A string that represents the game state for purpose of resolver and generator logs."""
        return self.damage_state.debug_string(self.resources)

    def collect_resource_node(self, node: ResourceNode, damage_state: DamageState) -> Self:
        """
        Creates a new State that has the given ResourceNode collected.
        :param node:
        :param damage_state: The state you should have when collecting this resource. Will add new resources to it.
        :return:
        """

        if not node.should_collect(self.node_context()):
            raise ValueError(f"Trying to collect an uncollectable node'{node}'")

        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(node.resource_gain_on_collect(self.node_context()))

        return State(
            new_resources,
            self.collected_resource_nodes + (node,),
            damage_state.apply_collected_resource_difference(new_resources, self.resources),
            self.node,
            self.patches,
            self,
        )

    def act_on_node(
        self, node: ResourceNode, path: tuple[Node, ...] = (), new_damage_state: DamageState | None = None
    ) -> Self:
        if new_damage_state is None:
            new_damage_state = self.damage_state
        new_state = self.collect_resource_node(node, new_damage_state)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    def assign_pickup_resources(self, pickup: PickupEntry) -> Self:
        return self.assign_pickups_resources([pickup])

    def assign_pickups_resources(self, pickups: Iterable[PickupEntry]) -> Self:
        new_resources = self.resources.duplicate()
        for pickup in pickups:
            new_resources.add_resource_gain(pickup.resource_gain(new_resources, force_lock=True))

        return State(
            new_resources,
            self.collected_resource_nodes,
            self.damage_state.apply_collected_resource_difference(new_resources, self.resources),
            self.node,
            self.patches,
            self,
        )

    def assign_pickup_to_starting_items(self, pickup: PickupEntry) -> Self:
        pickup_resources = ResourceCollection.from_resource_gain(
            self.resource_database, pickup.resource_gain(self.resources, force_lock=True)
        )

        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(pickup_resources.as_resource_gain())

        return State(
            new_resources,
            self.collected_resource_nodes,
            self.damage_state.apply_new_starting_resource_difference(new_resources, self.resources),
            self.node,
            self.patches.assign_extra_starting_pickups([pickup]),
            self,
        )

    def node_context(self) -> NodeContext:
        return NodeContext(
            self.patches,
            self.resources,
            self.resource_database,
            self.region_list,
        )


def add_pickup_to_state(state: State, pickup: PickupEntry):
    """
    Modifies inplace the given state, adding the resources of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    state.resources.add_resource_gain(pickup.resource_gain(state.resources, force_lock=True))
