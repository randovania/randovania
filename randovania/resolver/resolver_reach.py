from __future__ import annotations

import typing

from randovania.resolver import resolver_native

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.graph.graph_requirement import GraphRequirementList
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic


class ResolverReach:
    _data: resolver_native.ReachResult
    _logic: Logic

    def health_for_damage_requirements_at_node(self, index: int) -> int:
        return self._data.health_at(index)

    @property
    def satisfiable_requirements_for_additionals(self) -> set[GraphRequirementList]:
        return self._data.satisfiable_requirements_for_additionals

    def path_to_node(self, node: WorldGraphNode) -> tuple[WorldGraphNode, ...]:
        all_nodes = self._logic.world_specific[self._world_index].all_nodes
        path_to_node = self._data.path_to_node
        if node.node_index in path_to_node:
            return tuple(all_nodes[part] for part in path_to_node[node.node_index])
        else:
            return ()

    def __init__(
        self,
        logic: Logic,
        world_index: int,
        data: resolver_native.ReachResult,
    ):
        self._logic = logic
        self._world_index = world_index
        self._data = data

    @classmethod
    def calculate_reach(cls, logic: Logic, initial_state: State) -> ResolverReach:
        result = resolver_native.resolver_reach_process_nodes(logic, initial_state)
        return ResolverReach(logic, initial_state.world_index, result)

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        all_nodes = self._logic.world_specific[self._world_index].all_nodes
        return self._data.nodes(all_nodes)

    def is_node_in_reach(self, node: WorldGraphNode) -> bool:
        """True if the given node is part of `nodes`."""
        return self._data.is_node_in_reach(node.node_index)

    def collectable_resource_nodes(self, resources: ResourceCollection) -> Iterator[WorldGraphNode]:
        for node in self.nodes:
            if not node.has_all_resources(resources) and node.requirement_to_collect.satisfied(
                resources,
                self.health_for_damage_requirements_at_node(node.node_index),
            ):
                yield node

    def possible_actions(self, state: State) -> Iterator[tuple[WorldGraphNode, DamageState]]:
        for node in self.collectable_resource_nodes(state.resources):
            additional_requirements = self._logic.get_additional_requirements(state.world_index, node)
            health = self.health_for_damage_requirements_at_node(node.node_index)
            game_state = state.damage_state.with_health(health)
            if additional_requirements.satisfied(state.resources, health):
                yield node, game_state
            else:
                self._data.satisfiable_requirements_for_additionals = (
                    self._data.satisfiable_requirements_for_additionals.union(additional_requirements.alternatives)
                )
                self._logic.logger.log_skip(node, state, self._logic)
