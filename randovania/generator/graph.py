from __future__ import annotations

import copy
import itertools
import typing
from collections import defaultdict
from heapq import heappop, heappush
from typing import TYPE_CHECKING, override

import rustworkx

from randovania.graph.world_graph import WorldGraph

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable, Iterator, Mapping

    from randovania.game_description.db.node import NodeIndex
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement

    type GraphData = Requirement


class BaseGraph:
    @classmethod
    def new(cls, game: GameDescription) -> typing.Self:
        raise NotImplementedError

    def copy(self) -> typing.Self:
        raise NotImplementedError

    def add_node(self, node: int) -> None:
        raise NotImplementedError

    def add_edge(self, previous_node: NodeIndex, next_node: NodeIndex, data: GraphData) -> None:
        """Adds an edge between two nodes."""
        raise NotImplementedError

    def remove_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> None:
        """Removes a previously added edge. Raises if not present."""
        raise NotImplementedError

    def has_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> bool:
        """Checks if an edge exists between the two given nodes."""
        raise NotImplementedError

    def __contains__(self, item: NodeIndex) -> bool:
        """Checks if a given node index was added via `add_node`."""
        raise NotImplementedError

    def get_edge_data(self, previous_node: NodeIndex, next_node: NodeIndex) -> GraphData:
        """Gets the data that was added along the edge of the two given nodes."""
        raise NotImplementedError

    def edges_data(self) -> Iterator[tuple[NodeIndex, NodeIndex, GraphData]]:
        """Iterates over all edges that were added via `add_edge`."""
        raise NotImplementedError

    def shortest_paths_dijkstra(
        self,
        source: NodeIndex,
        weight: Callable[[NodeIndex, NodeIndex, GraphData], float],
    ) -> Mapping[int, float]:
        """
        Finds all nodes that are reachable from the given starting point.
        Returns a dict mapping found nodes to the cost of the path, with the cost of an edge being decided by `weight`.
        """
        raise NotImplementedError

    def strongly_connected_components(self) -> Iterable[Collection[NodeIndex]]:
        """
        Returns all strongly connected components of the graph.
        See https://en.wikipedia.org/wiki/Strongly_connected_component
        """
        raise NotImplementedError


class RandovaniaGraph(BaseGraph):
    edges: dict[int, dict[int, GraphData]]

    @override
    @classmethod
    def new(cls, game: GameDescription) -> typing.Self:
        return cls(defaultdict(dict))

    def __init__(self, edges: dict[int, dict[int, GraphData]]):
        self.edges = edges

    @override
    def copy(self) -> RandovaniaGraph:
        edges: dict[NodeIndex, dict[NodeIndex, GraphData]] = defaultdict(dict)
        edges.update({source: copy.copy(data) for source, data in self.edges.items()})
        return RandovaniaGraph(edges)

    @override
    def add_node(self, node: NodeIndex) -> None:
        if node not in self.edges:
            self.edges[node] = {}

    @override
    def add_edge(self, previous_node: NodeIndex, next_node: NodeIndex, data: GraphData) -> None:
        self.edges[previous_node][next_node] = data

    @override
    def remove_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> None:
        self.edges[previous_node].pop(next_node)

    @override
    def has_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> bool:
        return next_node in self.edges.get(previous_node, {})

    @override
    def __contains__(self, item: NodeIndex) -> bool:
        return item in self.edges

    @override
    def edges_data(self) -> Iterator[tuple[NodeIndex, NodeIndex, GraphData]]:
        for source, data in self.edges.items():
            for target, requirement in data.items():
                yield source, target, requirement

    @override
    def shortest_paths_dijkstra(
        self,
        source: NodeIndex,
        weight: Callable[[NodeIndex, NodeIndex, GraphData], float],
    ) -> Mapping[NodeIndex, float]:
        paths = {source: [source]}  # dictionary of paths
        edges = self.edges

        push = heappush
        pop = heappop

        dist: dict[int, float] = {}  # dictionary of final distances
        seen: dict[int, float] = {}
        # fringe is heapq with 3-tuples (distance,c,node)
        # use the count c to avoid comparing nodes (may not be able to)
        c = itertools.count()
        fringe: list[tuple[float, int, int]] = []
        seen[source] = 0
        push(fringe, (0, next(c), source))

        while fringe:
            (d, _, v) = pop(fringe)
            if v in dist:
                continue  # already searched this node.
            dist[v] = d
            for u, e in edges[v].items():
                cost = weight(v, u, e)
                if cost is None:
                    continue
                vu_dist = dist[v] + cost
                if u in dist:
                    u_dist = dist[u]
                    if vu_dist < u_dist:
                        raise ValueError("Contradictory paths found:", "negative weights?")
                elif u not in seen or vu_dist < seen[u]:
                    seen[u] = vu_dist
                    push(fringe, (vu_dist, next(c), u))
                    paths[u] = paths[v] + [u]

        return dist

    @override
    def strongly_connected_components(self) -> Iterable[Collection[NodeIndex]]:
        preorder = {}
        lowlink = {}
        scc_found = set()
        scc_queue: list[int] = []
        i = 0  # Preorder counter
        neighbors = {v: iter(self.edges[v]) for v in self.edges.keys()}
        for source in self.edges.keys():
            if source not in scc_found:
                queue = [source]
                while queue:
                    v = queue[-1]
                    if v not in preorder:
                        i = i + 1
                        preorder[v] = i
                    done = True
                    for w in neighbors[v]:
                        if w not in preorder:
                            queue.append(w)
                            done = False
                            break
                    if done:
                        lowlink[v] = preorder[v]
                        for w in self.edges[v].keys():
                            if w not in scc_found:
                                if preorder[w] > preorder[v]:
                                    lowlink[v] = min([lowlink[v], lowlink[w]])
                                else:
                                    lowlink[v] = min([lowlink[v], preorder[w]])
                        queue.pop()
                        if lowlink[v] == preorder[v]:
                            scc = {v}
                            while scc_queue and preorder[scc_queue[-1]] > preorder[v]:
                                k = scc_queue.pop()
                                scc.add(k)
                            scc_found.update(scc)
                            yield scc
                        else:
                            scc_queue.append(v)


class RustworkXGraph(BaseGraph):
    _graph: rustworkx.PyDiGraph
    _added_nodes: set[NodeIndex]

    @override
    @classmethod
    def new(cls, game: GameDescription | WorldGraph) -> typing.Self:
        g = rustworkx.PyDiGraph()
        if isinstance(game, WorldGraph):
            num_nodes = len(game.nodes)
        else:
            num_nodes = len(game.region_list.all_nodes)

        # rustworkx methods returns indices of the internal node list, instead of the data we passed
        # when creating the nodes. Instead of having to convert these indices, we'll instead just create all possible
        # nodes at once to guarantee the indices will always match.
        g.add_nodes_from(list(range(num_nodes)))
        return cls(g, set())

    def __init__(self, graph: rustworkx.PyDiGraph, added_nodes: set[NodeIndex]):
        self._graph = graph
        self._added_nodes = added_nodes

    @override
    def copy(self) -> RustworkXGraph:
        return RustworkXGraph(self._graph.copy(), self._added_nodes.copy())

    @override
    def add_node(self, node: NodeIndex) -> None:
        # Since `_graph` has all nodes always, we track added nodes separately just for the `__contains__` method.
        self._added_nodes.add(node)

    @override
    def add_edge(self, previous_node: NodeIndex, next_node: NodeIndex, data: GraphData) -> None:
        self._graph.add_edge(previous_node, next_node, (previous_node, next_node, data))

    @override
    def remove_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> None:
        self._graph.remove_edge(previous_node, next_node)

    @override
    def has_edge(self, previous_node: NodeIndex, next_node: NodeIndex) -> bool:
        return self._graph.has_edge(previous_node, next_node)

    @override
    def __contains__(self, item: NodeIndex) -> bool:
        return item in self._added_nodes

    def get_edge_data(self, previous_node: NodeIndex, next_node: NodeIndex) -> GraphData:
        return self._graph.get_edge_data(previous_node, next_node)[2]

    @override
    def edges_data(self) -> Iterator[tuple[NodeIndex, NodeIndex, GraphData]]:
        yield from self._graph.edges()

    @override
    def shortest_paths_dijkstra(
        self,
        source: NodeIndex,
        weight: Callable[[NodeIndex, NodeIndex, GraphData], float],
    ) -> Mapping[NodeIndex, float]:
        def wrap(data: tuple[NodeIndex, NodeIndex, GraphData]) -> float:
            return weight(*data)

        costs = dict(
            rustworkx.dijkstra_shortest_path_lengths(
                self._graph,
                source,
                edge_cost_fn=wrap,
            )
        )
        # Important to ensure the original node is present in the response
        costs[source] = 0.0
        return costs

    @override
    def strongly_connected_components(self) -> Iterable[Collection[NodeIndex]]:
        # Since we added every possible node already, this function returns a
        # bunch of additional components with just 1 array
        # All this does is make `_calculate_safe_nodes` slower.
        return rustworkx.strongly_connected_components(self._graph)
