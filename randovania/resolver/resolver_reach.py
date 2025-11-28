from __future__ import annotations

import typing

from randovania import _native

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
    _game_state_at_node: dict[int, DamageState]
    _path_to_node: dict[int, list[int]]
    _satisfiable_requirements_for_additionals: frozenset[GraphRequirementList]
    _logic: Logic

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        all_nodes = self._logic.all_nodes
        for index in self._node_indices:
            yield all_nodes[index]

    def game_state_at_node(self, index: int) -> DamageState:
        return self._game_state_at_node[index]

    @property
    def satisfiable_requirements_for_additionals(self) -> frozenset[GraphRequirementList]:
        return self._satisfiable_requirements_for_additionals

    def path_to_node(self, node: WorldGraphNode) -> tuple[WorldGraphNode, ...]:
        all_nodes = self._logic.all_nodes
        if node.node_index in self._path_to_node:
            return tuple(all_nodes[part] for part in self._path_to_node[node.node_index])
        else:
            return ()

    def __init__(
        self,
        nodes: dict[int, DamageState],
        path_to_node: dict[int, list[int]],
        requirements_for_additionals: frozenset[GraphRequirementList],
        logic: Logic,
    ):
        self._node_indices = tuple(nodes.keys())
        self._game_state_at_node = nodes
        self._logic = logic
        self._path_to_node = path_to_node
        self._satisfiable_requirements_for_additionals = requirements_for_additionals

    @classmethod
    def calculate_reach(cls, logic: Logic, initial_state: State) -> ResolverReach:
        # Keys: nodes to check
        # Value: how much energy was available when visiting that node
        nodes_to_check: dict[int, DamageState] = {initial_state.node.node_index: initial_state.damage_state}

        response = _native.resolver_reach_process_nodes(
            logic,
            initial_state,
            nodes_to_check,
        )
        reach_nodes = response.reach_nodes
        requirements_excluding_leaving_by_node = response.requirements_excluding_leaving_by_node

        # Discard satisfiable requirements of nodes reachable by other means
        for node_index in set(reach_nodes.keys()).intersection(requirements_excluding_leaving_by_node.keys()):
            requirements_excluding_leaving_by_node.pop(node_index)

        if requirements_excluding_leaving_by_node:
            satisfiable_requirements_for_additionals = _native.build_satisfiable_requirements(
                logic,
                requirements_excluding_leaving_by_node,
            )
        else:
            satisfiable_requirements_for_additionals = frozenset()

        return ResolverReach(reach_nodes, response.path_to_node, satisfiable_requirements_for_additionals, logic)

    def possible_actions(self, state: State) -> Iterator[tuple[WorldGraphNode, DamageState]]:
        for node in self.collectable_resource_nodes(state.resources):
            additional_requirements = self._logic.get_additional_requirements(node)
            game_state = self._game_state_at_node[node.node_index]
            if additional_requirements.satisfied(state.resources, game_state.health_for_damage_requirements()):
                yield node, game_state
            else:
                self._satisfiable_requirements_for_additionals = self._satisfiable_requirements_for_additionals.union(
                    additional_requirements.alternatives
                )
                self._logic.logger.log_skip(node, state, self._logic)

    def collectable_resource_nodes(self, resources: ResourceCollection) -> Iterator[WorldGraphNode]:
        for node in self.nodes:
            if not node.has_all_resources(resources) and node.requirement_to_collect.satisfied(
                resources,
                self._game_state_at_node[node.node_index].health_for_damage_requirements(),
            ):
                yield node
