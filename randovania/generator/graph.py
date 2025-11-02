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
    from collections.abc import Callable, Collection, Iterable, Iterator, Mapping, Sequence

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

    def add_edge(self, previous_node: int, next_node: int, data: GraphData) -> None:
        raise NotImplementedError

    def remove_edge(self, previous: int, target: int) -> None:
        raise NotImplementedError

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        raise NotImplementedError

    def __contains__(self, item: int) -> bool:
        raise NotImplementedError

    def edges_data(self) -> Iterator[tuple[int, int, GraphData]]:
        raise NotImplementedError

    has_multi_source_dijkstra = False

    def multi_source_dijkstra(
        self,
        sources: set[int],
        weight: Callable[[int, int, GraphData], int],
    ) -> tuple[dict[int, int], Mapping[int, Sequence[int]]]:
        raise NotImplementedError

    def shortest_paths_dijkstra(
        self,
        source: int,
        weight: Callable[[int, int, GraphData], int],
    ) -> Mapping[int, Sequence[int]]:
        _, paths = self.multi_source_dijkstra({source}, weight)
        return paths

    def strongly_connected_components(self) -> Iterable[Collection[int]]:
        raise NotImplementedError


class RandovaniaGraph(BaseGraph):
    edges: dict[int, dict[int, GraphData]]

    @override
    @classmethod
    def new(cls, game: GameDescription) -> typing.Self:
        return cls(defaultdict(dict))

    def __init__(self, edges: dict[int, dict[int, GraphData]]):
        self.edges = edges

    def copy(self) -> RandovaniaGraph:
        edges: dict[int, dict[int, GraphData]] = defaultdict(dict)
        edges.update({source: copy.copy(data) for source, data in self.edges.items()})
        return RandovaniaGraph(edges)

    def add_node(self, node: int) -> None:
        if node not in self.edges:
            self.edges[node] = {}

    def add_edge(self, previous_node: int, next_node: int, data: GraphData) -> None:
        self.edges[previous_node][next_node] = data

    def remove_edge(self, previous: int, target: int) -> None:
        self.edges[previous].pop(target)

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        return next_node in self.edges.get(previous_node, {})

    def __contains__(self, item: int) -> bool:
        return item in self.edges

    def edges_data(self) -> Iterator[tuple[int, int, GraphData]]:
        for source, data in self.edges.items():
            for target, requirement in data.items():
                yield source, target, requirement

    has_multi_source_dijkstra = True

    def multi_source_dijkstra(
        self,
        sources: set[int],
        weight: Callable[[int, int, GraphData], int],
    ) -> tuple[dict[int, int], Mapping[int, Sequence[int]]]:
        paths = {source: [source] for source in sources}  # dictionary of paths
        edges = self.edges

        push = heappush
        pop = heappop

        dist: dict[int, int] = {}  # dictionary of final distances
        seen = {}
        # fringe is heapq with 3-tuples (distance,c,node)
        # use the count c to avoid comparing nodes (may not be able to)
        c = itertools.count()
        fringe: list[tuple[int, int, int]] = []
        for source in sources:
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

        return dist, paths

    def strongly_connected_components(self) -> Iterable[Collection[int]]:
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
    _added_nodes: set[int]

    @override
    @classmethod
    def new(cls, game: GameDescription | WorldGraph) -> typing.Self:
        g = rustworkx.PyDiGraph()
        if isinstance(game, WorldGraph):
            num_nodes = len(game.nodes)
        else:
            num_nodes = len(game.region_list.all_nodes)

        g.add_nodes_from(list(range(num_nodes)))
        return cls(g, set())

    def __init__(self, graph: rustworkx.PyDiGraph, added_nodes: set[int]):
        self._graph = graph
        self._added_nodes = added_nodes

    def copy(self) -> RustworkXGraph:
        return RustworkXGraph(self._graph.copy(), self._added_nodes.copy())

    def add_node(self, node: int) -> None:
        self._added_nodes.add(node)

    def add_edge(self, previous_node: int, next_node: int, data: GraphData) -> None:
        self._graph.add_edge(previous_node, next_node, (previous_node, next_node, data))

    def remove_edge(self, previous_node: int, next_node: int) -> None:
        self._graph.remove_edge(previous_node, next_node)

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        return self._graph.has_edge(previous_node, next_node)

    def __contains__(self, item: int) -> bool:
        return item in self._added_nodes

    def edges_data(self) -> Iterator[tuple[int, int, GraphData]]:
        yield from self._graph.edges()

    def multi_source_dijkstra(
        self,
        sources: set[int],
        weight: Callable[[int, int, GraphData], int],
    ) -> tuple[dict[int, int], Mapping[int, Sequence[int]]]:
        raise NotImplementedError

    def shortest_paths_dijkstra(
        self,
        source: int,
        weight: Callable[[int, int, GraphData], int],
    ) -> Mapping[int, Sequence[int]]:
        def wrap(data: tuple[int, int, GraphData]) -> float:
            return weight(*data)

        paths: dict[int, Sequence[int]] = dict(
            rustworkx.dijkstra_shortest_paths(
                self._graph,
                source,
                weight_fn=wrap,
            )
        )
        paths[source] = [source]
        return paths

    def strongly_connected_components(self) -> Iterable[Collection[int]]:
        return rustworkx.strongly_connected_components(self._graph)
