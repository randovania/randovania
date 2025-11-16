from __future__ import annotations

import copy
import functools
import typing
from typing import TYPE_CHECKING, Self, override

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.generator import graph as graph_module
from randovania.generator.generator_reach import GeneratorReach
from randovania.graph.state import GraphOrResourceNode
from randovania.graph.world_graph import WorldGraph, WorldGraphNode

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Mapping, Sequence

    from randovania.game_description.db.node import Node, NodeContext, NodeIndex
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.graph.state import GraphOrClassicNode, State


def _extra_requirement_for_node(
    game: GameDescription | WorldGraph, context: NodeContext, node: GraphOrClassicNode
) -> Requirement | None:
    extra_requirement = None

    if node.is_resource_node():
        assert isinstance(node, GraphOrResourceNode)
        dangerous_extra = [
            ResourceRequirement.simple(resource)
            for resource, quantity in node.resource_gain_on_collect(context)
            if resource in game.dangerous_resources
        ]
        if dangerous_extra:
            extra_requirement = RequirementAnd(dangerous_extra)

    return extra_requirement


class GraphPath:
    __slots__ = ("previous_node", "node", "requirement")
    previous_node: NodeIndex | None
    node: NodeIndex
    requirement: Requirement

    def __init__(self, previous: NodeIndex | None, node: NodeIndex, requirement: Requirement):
        self.previous_node = previous
        self.node = node
        self.requirement = requirement

    def is_in_graph(self, digraph: graph_module.BaseGraph) -> bool:
        if self.previous_node is None:
            return False
        else:
            return digraph.has_edge(self.previous_node, self.node)

    def add_to_graph(self, digraph: graph_module.BaseGraph) -> None:
        digraph.add_node(self.node)
        if self.previous_node is not None:
            digraph.add_edge(self.previous_node, self.node, data=self.requirement)


class _SafeNodes:
    as_list: list[int]
    as_set: set[int]

    def __init__(self, component: Collection[NodeIndex]):
        self.as_list = sorted(component)
        self.as_set = set(component)


class OldGeneratorReach(GeneratorReach):
    _digraph: graph_module.BaseGraph
    _state: State
    _game: GameDescription | WorldGraph
    _reachable_costs: Mapping[int, float] | None
    _node_reachable_cache: dict[int, bool]
    _unreachable_paths: dict[tuple[int, int], Requirement]
    _uncollectable_nodes: dict[int, Requirement]
    _safe_nodes: _SafeNodes | None
    _is_node_safe_cache: dict[int, bool]
    _filler_config: FillerConfiguration
    all_nodes: Sequence[GraphOrClassicNode]

    def __deepcopy__(self, memodict: dict) -> OldGeneratorReach:
        reach = OldGeneratorReach(self._game, self._state, self._digraph.copy(), copy.copy(self._filler_config))
        reach._unreachable_paths = copy.copy(self._unreachable_paths)
        reach._uncollectable_nodes = copy.copy(self._uncollectable_nodes)
        reach._reachable_costs = self._reachable_costs
        reach._safe_nodes = self._safe_nodes

        reach._node_reachable_cache = copy.copy(self._node_reachable_cache)
        reach._is_node_safe_cache = copy.copy(self._is_node_safe_cache)
        return reach

    def __init__(
        self,
        game: GameDescription | WorldGraph,
        state: State,
        graph: graph_module.BaseGraph,
        filler_config: FillerConfiguration,
    ):
        self._game = game
        if isinstance(game, GameDescription):
            self.all_nodes = typing.cast("Sequence[GraphOrClassicNode]", game.region_list.all_nodes)
        else:
            self.all_nodes = typing.cast("Sequence[GraphOrClassicNode]", game.nodes)

        self._state = state
        self._digraph = graph
        self._unreachable_paths = {}
        self._uncollectable_nodes = {}
        self._reachable_costs = None
        self._node_reachable_cache = {}
        self._is_node_safe_cache = {}
        self._filler_config = filler_config

    @classmethod
    def reach_from_state(
        cls,
        game: GameDescription | WorldGraph,
        initial_state: State,
        filler_config: FillerConfiguration,
    ) -> Self:
        reach = cls(game, initial_state, graph_module.RustworkXGraph.new(game), filler_config)
        if isinstance(game, GameDescription):
            game.region_list.ensure_has_node_cache()
        reach._expand_graph([GraphPath(None, initial_state.node.node_index, Requirement.trivial())])
        return reach

    def _potential_nodes_from(
        self, node: GraphOrClassicNode, context: NodeContext
    ) -> list[tuple[GraphOrClassicNode, Requirement]]:
        extra_requirement = _extra_requirement_for_node(self._game, context, node)

        connections: list[tuple[GraphOrClassicNode, Requirement]]

        if isinstance(node, WorldGraphNode):
            connections = [
                (
                    conn.target,
                    conn.requirement
                    if extra_requirement is None
                    else RequirementAnd([conn.requirement, extra_requirement]),
                )
                for conn in node.connections
            ]
        else:
            assert isinstance(self._game, GameDescription)
            connections = []

            requirement_to_leave = node.requirement_to_leave(context)
            for target_node, requirement in self._game.region_list.potential_nodes_from(node, context):
                if target_node is None:
                    continue

                if requirement_to_leave != Requirement.trivial():
                    requirement = RequirementAnd([requirement, requirement_to_leave])

                if extra_requirement is not None:
                    requirement = RequirementAnd([requirement, extra_requirement])

                connections.append((target_node, requirement))

        return connections

    def _expand_graph(self, paths_to_check: list[GraphPath]) -> None:
        # print("!! _expand_graph", len(paths_to_check))
        self._reachable_costs = None
        resource_nodes_to_check = set()

        all_nodes = self.all_nodes
        context = self._state.node_context()

        while paths_to_check:
            path = paths_to_check.pop(0)

            if path.is_in_graph(self._digraph):
                # print(">>> already in graph", path.node.full_name())
                continue

            # print(">>> will check starting at", path.node.full_name())
            path.add_to_graph(self._digraph)

            if all_nodes[path.node].is_resource_node():
                resource_nodes_to_check.add(path.node)

            for target_node, requirement in self._potential_nodes_from(all_nodes[path.node], context):
                target_node_index = target_node.node_index

                # is_in_graph inlined, so we don't need to create GraphPath
                if self._digraph.has_edge(path.node, target_node_index):
                    continue

                if requirement.satisfied(context, self._state.health_for_damage_requirements):
                    # print("* Queue path to", target_node.full_name())
                    paths_to_check.append(GraphPath(path.node, target_node_index, requirement))
                else:
                    # print("* Unreachable", self.game.region_list.node_name(target_node), ", missing:",
                    #       requirement.as_str)
                    self._unreachable_paths[path.node, target_node_index] = requirement
            # print("> done")

        for node_index in sorted(resource_nodes_to_check):
            node = self.all_nodes[node_index]
            assert isinstance(node, ResourceNode | WorldGraphNode)

            requirement = node.requirement_to_collect
            if not requirement.satisfied(context, self._state.health_for_damage_requirements):
                self._uncollectable_nodes[node_index] = requirement

        # print("!! _expand_graph finished. Has {} edges".format(sum(1 for _ in self._digraph.edges_data())))
        self._safe_nodes = None

    def _can_advance(
        self,
        node: GraphOrClassicNode,
    ) -> bool:
        """
        Calculates if we can advance past a given node
        :param node:
        :return:
        """
        # We can't advance past a resource node if we haven't collected it
        if node.is_resource_node():
            assert isinstance(node, GraphOrResourceNode)
            return node.is_collected(self.node_context())
        else:
            return True

    def _calculate_safe_nodes(self) -> None:
        if self._safe_nodes is not None:
            return

        for component in self._digraph.strongly_connected_components():
            if self._state.node.node_index in component:
                assert self._safe_nodes is None
                self._safe_nodes = _SafeNodes(component)

        assert self._safe_nodes is not None

    def _calculate_reachable_costs(self) -> None:
        if self._reachable_costs is not None:
            return

        context = self.node_context()

        if isinstance(self._game, WorldGraph):
            graph_nodes = self._game.nodes

            @functools.cache
            def _is_collected(target: int) -> int:
                return not graph_nodes[target].is_collected(context)
        else:
            db_nodes = typing.cast("tuple[Node, ...]", self._game.region_list.all_nodes)

            @functools.cache
            def _is_collected(target: int) -> int:
                node = db_nodes[target]
                if node.is_resource_node():
                    if typing.cast("ResourceNode", node).is_collected(context):
                        return 0
                    else:
                        return 1
                else:
                    return 0

        self._reachable_is_collected = _is_collected

        def weight(source: int, target: int, attributes: graph_module.GraphData) -> int:
            return _is_collected(target)

        self._reachable_costs = self._digraph.shortest_paths_dijkstra(
            self._state.node.node_index,
            weight=weight,
        )

    def set_of_reachable_node_indices(self) -> set[int]:
        self._calculate_reachable_costs()
        assert self._reachable_costs is not None
        return {index for index in self._reachable_costs.keys() if self.is_reachable_node_index(index)}

    def is_reachable_node(self, node: GraphOrClassicNode) -> bool:
        return self.is_reachable_node_index(node.node_index)

    def is_reachable_node_index(self, index: int) -> bool:
        cached_value = self._node_reachable_cache.get(index)
        if cached_value is not None:
            return cached_value

        self._calculate_reachable_costs()
        assert self._reachable_costs is not None
        if index in self._reachable_costs:
            cost = self._reachable_costs[index]
            if cost == 0:
                self._node_reachable_cache[index] = True
            elif cost == 1:
                self._node_reachable_cache[index] = not self._can_advance(self.all_nodes[index])
            else:
                self._node_reachable_cache[index] = False

            return self._node_reachable_cache[index]
        else:
            return False

    @property
    def connected_nodes(self) -> Iterator[GraphOrClassicNode]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        self._calculate_reachable_costs()
        assert self._reachable_costs is not None
        all_nodes = self.all_nodes
        for index in self._reachable_costs.keys():
            yield all_nodes[index]

    @property
    def state(self) -> State:
        return self._state

    @property
    def game(self) -> GameDescription | WorldGraph:
        return self._game

    @property
    def nodes(self) -> Iterator[GraphOrClassicNode]:
        for i, node in enumerate(self.all_nodes):
            if i in self._digraph:
                yield node

    @property
    def safe_nodes(self) -> Iterator[GraphOrClassicNode]:
        self._calculate_safe_nodes()
        assert self._safe_nodes is not None

        all_nodes = self.all_nodes
        for i in self._safe_nodes.as_list:
            yield all_nodes[i]

    def is_safe_node(self, node: GraphOrClassicNode) -> bool:
        node_index = node.node_index
        is_safe = self._is_node_safe_cache.get(node_index)
        if is_safe is not None:
            return is_safe

        self._calculate_safe_nodes()
        assert self._safe_nodes is not None
        self._is_node_safe_cache[node_index] = node_index in self._safe_nodes.as_set
        return self._is_node_safe_cache[node_index]

    def advance_to(
        self,
        new_state: State,
        is_safe: bool = False,
    ) -> None:
        assert new_state.previous_state == self._state
        # assert self.is_reachable_node(new_state.node)

        if is_safe or self.is_safe_node(new_state.node):
            for index in [index for index, flag in self._node_reachable_cache.items() if not flag]:
                del self._node_reachable_cache[index]

            for node_index in [node_index for node_index, flag in self._is_node_safe_cache.items() if not flag]:
                del self._is_node_safe_cache[node_index]
        else:
            self._node_reachable_cache = {}
            self._is_node_safe_cache = {}

        self._state = new_state

        paths_to_check: list[GraphPath] = []

        edges_to_remove = []
        # Check if we can expand the corners of our graph
        # TODO: check if expensive. We filter by only nodes that depends on a new resource
        for edge, requirement in self._unreachable_paths.items():
            if requirement.satisfied(self._state.node_context(), self._state.health_for_damage_requirements):
                from_index, to_index = edge
                paths_to_check.append(GraphPath(from_index, to_index, requirement))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        for node_index, requirement in list(self._uncollectable_nodes.items()):
            if requirement.satisfied(self._state.node_context(), self._state.health_for_damage_requirements):
                del self._uncollectable_nodes[node_index]

        self._expand_graph(paths_to_check)

    def act_on(self, node: GraphOrResourceNode) -> None:
        new_dangerous_resources = {
            resource
            for resource, quantity in node.resource_gain_on_collect(self._state.node_context())
            if resource in self.game.dangerous_resources
        }
        new_state = self._state.act_on_node(node)

        context = new_state.node_context()

        def _dangerous_requirements(req: Requirement) -> set[ResourceInfo]:
            return {indiv.resource for indiv in req.iterate_resource_requirements(context) if indiv.negate}

        if new_dangerous_resources:
            edges_to_remove = []
            for source, target, requirement in self._digraph.edges_data():
                if not new_dangerous_resources.isdisjoint(_dangerous_requirements(requirement)):
                    if not requirement.satisfied(context, new_state.health_for_damage_requirements):
                        edges_to_remove.append((source, target))

            for edge in edges_to_remove:
                self._digraph.remove_edge(*edge)

        self.advance_to(new_state)

    def unreachable_nodes_with_requirements(self) -> dict[NodeIndex, RequirementSet]:
        results: dict[NodeIndex, RequirementSet] = {}
        all_nodes = self.all_nodes
        context = self._state.node_context()

        to_check = [
            (all_nodes[node_index], requirement) for node_index, requirement in self._uncollectable_nodes.items()
        ]

        for (source_node_index, target_node_index), requirement in self._unreachable_paths.items():
            source_node = all_nodes[source_node_index]
            target_node = all_nodes[target_node_index]
            if self.is_reachable_node(source_node) and not self.is_reachable_node(target_node):
                to_check.append((target_node, requirement))

        for node, requirement in to_check:
            requirements = requirement.patch_requirements(1.0, context).as_set(context)
            if node.node_index in results:
                results[node.node_index] = results[node.node_index].expand_alternatives(requirements)
            else:
                results[node.node_index] = requirements

        return results

    def victory_condition_satisfied(self) -> bool:
        context = self._state.node_context()
        return self.game.victory_condition_as_set(context).satisfied(
            context, self._state.health_for_damage_requirements
        )

    @override
    @property
    def filler_config(self) -> FillerConfiguration:
        return self._filler_config

    @filler_config.setter
    def filler_config(self, config: FillerConfiguration) -> None:
        self._filler_config = config
