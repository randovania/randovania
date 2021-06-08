import copy
import itertools
from heapq import heappush, heappop
from typing import Dict, Iterator, Tuple, Set, Callable

from randovania.game_description.requirements import RequirementSet


class BaseGraph:
    def copy(self):
        raise NotImplementedError()

    def add_node(self, node: int):
        raise NotImplementedError()

    def add_edge(self, previous_node: int, next_node: int, requirement: RequirementSet):
        raise NotImplementedError()

    def remove_edge(self, previous: int, target: int):
        raise NotImplementedError()

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        raise NotImplementedError()

    def __contains__(self, item: int):
        raise NotImplementedError()

    def edges_data(self) -> Iterator[Tuple[int, int, RequirementSet]]:
        raise NotImplementedError()

    def multi_source_dijkstra(self, sources: Set[int], weight: Callable[[int, int, RequirementSet], float]):
        raise NotImplementedError()

    def single_source_dijkstra_path(self, source: int):
        raise NotImplementedError()

    def strongly_connected_components(self) -> Iterator[Set[int]]:
        raise NotImplementedError()


class RandovaniaGraph(BaseGraph):
    edges: Dict[int, Dict[int, RequirementSet]]

    @classmethod
    def new(cls):
        return cls({})

    def __init__(self, edges: Dict[int, Dict[int, RequirementSet]]):
        import networkx
        self.networkx = networkx
        self.edges = edges

    def copy(self):
        return RandovaniaGraph(
            {
                source: copy.copy(data)
                for source, data in self.edges.items()
            },
        )

    def add_node(self, node: int):
        if node not in self.edges:
            self.edges[node] = {}

    def add_edge(self, previous_node: int, next_node: int, requirement: RequirementSet):
        self.edges[previous_node][next_node] = requirement

    def remove_edge(self, previous: int, target: int):
        self.edges[previous].pop(target)

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        return next_node in self.edges.get(previous_node, {})

    def __contains__(self, item: int):
        return item in self.edges

    def edges_data(self):
        for source, data in self.edges.items():
            for target, requirement in data.items():
                yield source, target, requirement

    def multi_source_dijkstra(self, sources: Set[int], weight: Callable[[int, int, RequirementSet], float]):
        paths = {source: [source] for source in sources}  # dictionary of paths
        edges = self.edges

        push = heappush
        pop = heappop

        dist = {}  # dictionary of final distances
        seen = {}
        # fringe is heapq with 3-tuples (distance,c,node)
        # use the count c to avoid comparing nodes (may not be able to)
        c = itertools.count()
        fringe = []
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

    def single_source_dijkstra_path(self, source: int):
        length, path = self.multi_source_dijkstra({source}, weight=lambda s, t, req: 1)
        return path

    def strongly_connected_components(self) -> Iterator[Set[int]]:
        preorder = {}
        lowlink = {}
        scc_found = set()
        scc_queue = []
        i = 0  # Preorder counter
        for source in self.edges.keys():
            if source not in scc_found:
                queue = [source]
                while queue:
                    v = queue[-1]
                    if v not in preorder:
                        i = i + 1
                        preorder[v] = i
                    done = True
                    for w in self.edges[v].keys():
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
