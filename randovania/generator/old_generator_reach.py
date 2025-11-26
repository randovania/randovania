from __future__ import annotations

import copy
import functools
import itertools
import typing
from typing import TYPE_CHECKING, Self, override

import rustworkx

from randovania import _native
from randovania.generator.generator_reach import GeneratorReach
from randovania.graph.graph_requirement import GraphRequirementSet

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence

    from randovania.game_description.db.node import NodeIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode

    type GraphData = GraphRequirementSet


class RustworkXGraph:
    graph: rustworkx.PyDiGraph
    _added_nodes: set[NodeIndex]

    @classmethod
    def new(cls, game: WorldGraph) -> typing.Self:
        g = rustworkx.PyDiGraph()
        num_nodes = len(game.nodes)

        # rustworkx methods returns indices of the internal node list, instead of the data we passed
        # when creating the nodes. Instead of having to convert these indices, we'll instead just create all possible
        # nodes at once to guarantee the indices will always match.
        g.add_nodes_from(list(range(num_nodes)))
        return cls(g, set())

    def __init__(self, graph: rustworkx.PyDiGraph, added_nodes: set[NodeIndex]):
        self.graph = graph
        self._added_nodes = added_nodes

    def copy(self) -> RustworkXGraph:
        return RustworkXGraph(self.graph.copy(), self._added_nodes.copy())

    def add_node(self, node: NodeIndex) -> None:
        # Since `_graph` has all nodes always, we track added nodes separately just for the `__contains__` method.
        self._added_nodes.add(node)

    def add_edge(self, previous_node: NodeIndex, next_node: NodeIndex, data: GraphData) -> None:
        self.graph.add_edge(previous_node, next_node, (previous_node, next_node, data))

    def remove_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> None:
        self.graph.remove_edge(previous_node, next_node)

    def has_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> bool:
        return self.graph.has_edge(previous_node, next_node)

    def __contains__(self, item: NodeIndex) -> bool:
        return item in self._added_nodes

    def get_edge_data(self, previous_node: NodeIndex, next_node: NodeIndex) -> GraphData:
        return self.graph.get_edge_data(previous_node, next_node)[2]

    def edges_data(self) -> Iterator[tuple[NodeIndex, NodeIndex, GraphData]]:
        yield from self.graph.edges()

    def shortest_paths_dijkstra(
        self,
        source: NodeIndex,
        weight: Callable[[NodeIndex, NodeIndex, GraphData], float],
    ) -> Mapping[NodeIndex, float]:
        def wrap(data: tuple[NodeIndex, NodeIndex, GraphData]) -> float:
            return weight(*data)

        costs = dict(
            rustworkx.dijkstra_shortest_path_lengths(
                self.graph,
                source,
                edge_cost_fn=wrap,
            )
        )
        # Important to ensure the original node is present in the response
        costs[source] = 0.0
        return costs

    def strongly_connected_components(self) -> Iterable[Collection[NodeIndex]]:
        # Since we added every possible node already, this function returns a
        # bunch of additional components with just 1 array
        # All this does is make `_calculate_safe_nodes` slower.
        return rustworkx.strongly_connected_components(self.graph)


class GraphPath:
    __slots__ = ("previous_node", "node", "requirement")
    previous_node: NodeIndex | None
    node: NodeIndex
    requirement: GraphRequirementSet

    def __init__(self, previous: NodeIndex | None, node: NodeIndex, requirement: GraphRequirementSet):
        self.previous_node = previous
        self.node = node
        self.requirement = requirement


class _SafeNodes:
    as_list: list[NodeIndex]
    as_set: set[NodeIndex]

    def __init__(self, component: Collection[NodeIndex]):
        self.as_list = sorted(component)
        self.as_set = set(component)


def _new_resources_including_damage(state: State) -> set[ResourceInfo]:
    """
    Returns all new resources of the given state, plus any damage resources that are impacted by
    having more health or more damage reduction (global or specific).
    """
    damage_state = state.damage_state
    new_resources = set(state.new_resources)
    if new_resources & set(
        itertools.chain(damage_state.resources_for_health(), damage_state.resources_for_general_reduction())
    ):
        for damage_res in state.resource_database.damage:
            new_resources.add(damage_res)
    else:
        for res, reductions in state.resource_database.damage_reductions.items():
            if any(reduction.inventory_item in new_resources for reduction in reductions):
                new_resources.add(res)

    return new_resources


class OldGeneratorReach(GeneratorReach):
    _digraph: RustworkXGraph
    _state: State
    _graph: WorldGraph
    _reachable_costs: Mapping[int, float] | None
    _node_reachable_cache: dict[int, bool]
    _unreachable_paths: dict[tuple[int, int], GraphRequirementSet]
    _uncollectable_nodes: dict[int, GraphRequirementSet]
    _safe_nodes: _SafeNodes | None
    _is_node_safe_cache: dict[int, bool]
    _filler_config: FillerConfiguration
    all_nodes: Sequence[WorldGraphNode]

    def __deepcopy__(self, memodict: dict) -> OldGeneratorReach:
        reach = OldGeneratorReach(self._graph, self._state, self._digraph.copy(), copy.copy(self._filler_config))
        reach._unreachable_paths = copy.copy(self._unreachable_paths)
        reach._uncollectable_nodes = copy.copy(self._uncollectable_nodes)
        reach._reachable_costs = self._reachable_costs
        reach._safe_nodes = self._safe_nodes

        reach._node_reachable_cache = copy.copy(self._node_reachable_cache)
        reach._is_node_safe_cache = copy.copy(self._is_node_safe_cache)
        return reach

    def __init__(
        self,
        game: WorldGraph,
        state: State,
        digraph: RustworkXGraph,
        filler_config: FillerConfiguration,
    ):
        self._graph = game
        self.all_nodes = game.nodes

        self._state = state
        self._digraph = digraph
        self._unreachable_paths = {}
        self._uncollectable_nodes = {}
        self._reachable_costs = None
        self._node_reachable_cache = {}
        self._is_node_safe_cache = {}
        self._filler_config = filler_config

    @classmethod
    def reach_from_state(
        cls,
        graph: WorldGraph,
        initial_state: State,
        filler_config: FillerConfiguration,
    ) -> Self:
        reach = cls(graph, initial_state, RustworkXGraph.new(graph), filler_config)
        reach._expand_graph([GraphPath(None, initial_state.node.node_index, GraphRequirementSet.trivial())])
        return reach

    def _expand_graph(self, paths_to_check: list[GraphPath]) -> None:
        # print("!! _expand_graph", len(paths_to_check))
        self._reachable_costs = None

        _native.generator_reach_expand_graph(
            self._state,
            self._graph,
            self._digraph,
            paths_to_check,
            self._unreachable_paths,
            self._uncollectable_nodes,
        )

        # print("!! _expand_graph finished. Has {} edges".format(sum(1 for _ in self._digraph.edges_data())))
        self._safe_nodes = None

    def _can_advance(
        self,
        node: WorldGraphNode,
    ) -> bool:
        """
        Calculates if we can advance past a given node
        :param node:
        :return:
        """
        # We can't advance past a resource node if we haven't collected it
        return node.has_all_resources(self.state.resources)

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

        resources = self.state.resources

        @functools.cache
        def _is_collected(target: int) -> int:
            node = self.all_nodes[target]
            if node.has_all_resources(resources):
                return 0
            else:
                return 1

        def weight(source: int, target: int, attributes: GraphData) -> int:
            return _is_collected(target)

        self._reachable_costs = self._digraph.shortest_paths_dijkstra(
            self._state.node.node_index,
            weight=weight,
        )

    def set_of_reachable_node_indices(self) -> set[int]:
        self._calculate_reachable_costs()
        assert self._reachable_costs is not None
        return {index for index in self._reachable_costs.keys() if self.is_reachable_node_index(index)}

    def is_reachable_node(self, node: WorldGraphNode) -> bool:
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
    def connected_nodes(self) -> Iterator[WorldGraphNode]:
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
    def graph(self) -> WorldGraph:
        return self._graph

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        for i, node in enumerate(self.all_nodes):
            if i in self._digraph:
                yield node

    @property
    def safe_nodes(self) -> Iterator[WorldGraphNode]:
        self._calculate_safe_nodes()
        assert self._safe_nodes is not None

        all_nodes = self.all_nodes
        for i in self._safe_nodes.as_list:
            yield all_nodes[i]

    @property
    @override
    def safe_nodes_index_set(self) -> set[int]:
        self._calculate_safe_nodes()
        assert self._safe_nodes is not None
        return self._safe_nodes.as_set

    def is_safe_node(self, node: WorldGraphNode) -> bool:
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
        health = self._state.health_for_damage_requirements
        resources = self._state.resources

        # Collect edges to check based on the new resources
        possible_edges: set[tuple[int, int]] = set()

        for resource in _new_resources_including_damage(new_state):
            possible_edges.update(self.graph.resource_to_edges.get(resource, []))

        # Check if we can expand the corners of our graph
        paths_to_check: list[GraphPath] = []
        for edge in possible_edges:
            requirement = self._unreachable_paths.get(edge)
            if requirement is not None and requirement.satisfied(resources, health):
                from_index, to_index = edge
                paths_to_check.append(GraphPath(from_index, to_index, requirement))
                del self._unreachable_paths[edge]

        # Delay updating _uncollectable_nodes until it's used, as it's faster that way

        self._expand_graph(paths_to_check)

    def act_on(self, node: WorldGraphNode) -> None:
        new_state = self._state.act_on_node(node)
        resources = new_state.resources

        new_dangerous_resources = {
            resource for resource in new_state.new_resources if resource in self.graph.dangerous_resources
        }

        edges_to_check: set[tuple[NodeIndex, NodeIndex]] = set()

        for resource in new_dangerous_resources:
            edges_to_check.update(self.graph.resource_to_dangerous_edges[resource])

        # TODO: This can easily be part of `advance_to` now.
        for source, target in edges_to_check:
            if self._digraph.has_edge(source, target):
                requirement = self._digraph.get_edge_data(source, target)
                if not requirement.satisfied(resources, new_state.health_for_damage_requirements):
                    self._digraph.remove_edge(source, target)

        self.advance_to(new_state)

    def unreachable_nodes_with_requirements(self) -> dict[NodeIndex, GraphRequirementSet]:
        results: dict[NodeIndex, GraphRequirementSet] = {}
        resources = self._state.resources

        to_check: list[tuple[NodeIndex, GraphRequirementSet]] = []

        # Check uncollectable nodes. It might be outdated since advance_to skips updating, so handle that
        for node_index, requirement in list(self._uncollectable_nodes.items()):
            if requirement.satisfied(resources, self._state.health_for_damage_requirements):
                self._uncollectable_nodes.pop(node_index, None)
            elif self.is_reachable_node_index(node_index):
                to_check.append((node_index, requirement))

        for (source_node_index, target_node_index), requirement in self._unreachable_paths.items():
            if self.is_reachable_node_index(source_node_index) and not self.is_reachable_node_index(target_node_index):
                to_check.append((target_node_index, requirement))

        for node_index, requirement in to_check:
            # Remove individual resources from `requirement` that are already present
            # TODO: might actually be completely useless!
            requirement = requirement.copy_then_remove_entries_for_set_resources(resources)
            if node_index in results:
                results[node_index].extend_alternatives(requirement.alternatives)
                # TODO: check if calling optimize_alternatives helps
            else:
                results[node_index] = requirement

        return results

    @override
    @property
    def filler_config(self) -> FillerConfiguration:
        return self._filler_config

    @filler_config.setter
    def filler_config(self, config: FillerConfiguration) -> None:
        self._filler_config = config
