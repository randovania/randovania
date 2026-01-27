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
    _node_indices: tuple[int, ...]
    _health_at_node: dict[int, int]
    _path_to_node: dict[int, list[int]]
    _satisfiable_requirements_for_additionals: set[GraphRequirementList]
    _logic: Logic

    def health_for_damage_requirements_at_node(self, index: int) -> int:
        return self._health_at_node[index]

    @property
    def satisfiable_requirements_for_additionals(self) -> set[GraphRequirementList]:
        return self._satisfiable_requirements_for_additionals

    def path_to_node(self, node: WorldGraphNode) -> tuple[WorldGraphNode, ...]:
        all_nodes = self._logic.all_nodes
        if node.node_index in self._path_to_node:
            return tuple(all_nodes[part] for part in self._path_to_node[node.node_index])
        else:
            return ()

    def __init__(
        self,
        logic: Logic,
        data: resolver_native.ProcessNodesResponse,
    ):
        self._logic = logic
        self._node_indices = tuple(data.reach_nodes.keys())
        self._health_at_node = data.reach_nodes
        self._path_to_node = data.path_to_node
        self._satisfiable_requirements_for_additionals = data.satisfiable_requirements_for_additionals

    @classmethod
    def calculate_reach(cls, logic: Logic, initial_state: State) -> ResolverReach:
        response = resolver_native.ProcessNodesResponse(
            reach_nodes={},
            path_to_node={},
            satisfiable_requirements_for_additionals=set(),
        )
        resolver_native.resolver_reach_process_nodes(
            logic,
            initial_state,
            response,
        )
        return ResolverReach(logic, response)

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        all_nodes = self._logic.all_nodes
        for index in self._node_indices:
            yield all_nodes[index]

    def is_node_in_reach(self, node: WorldGraphNode) -> bool:
        """True if the given node is part of `nodes`."""
        return node.node_index in self._health_at_node

    def collectable_resource_nodes(self, resources: ResourceCollection) -> Iterator[WorldGraphNode]:
        for node in self.nodes:
            if not node.has_all_resources(resources) and node.requirement_to_collect.satisfied(
                resources,
                self.health_for_damage_requirements_at_node(node.node_index),
            ):
                yield node

    def possible_actions(self, state: State) -> Iterator[tuple[WorldGraphNode, DamageState]]:
        for node in self.collectable_resource_nodes(state.resources):
            additional_requirements = self._logic.get_additional_requirements(node)
            health = self.health_for_damage_requirements_at_node(node.node_index)
            game_state = state.damage_state.with_health(health)
            if additional_requirements.satisfied(state.resources, health):
                yield node, game_state
            else:
                self._satisfiable_requirements_for_additionals = self._satisfiable_requirements_for_additionals.union(
                    additional_requirements.alternatives
                )
                self._logic.logger.log_skip(node, state, self._logic)
