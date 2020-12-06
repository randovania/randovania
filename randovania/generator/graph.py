import copy
from typing import Dict, Iterator, Tuple, Set, Callable

import networkx

from randovania.game_description.requirements import Requirement


class BaseGraph:
    def copy(self):
        raise NotImplementedError()

    def add_node(self, node: int):
        raise NotImplementedError()

    def add_edge(self, previous_node: int, next_node: int, requirement: Requirement):
        raise NotImplementedError()

    def remove_edge(self, previous: int, target: int):
        raise NotImplementedError()

    def has_edge(self, previous_node: int, next_node: int) -> bool:
        raise NotImplementedError()

    def __contains__(self, item: int):
        raise NotImplementedError()

    def edges_data(self) -> Iterator[Tuple[int, int, Requirement]]:
        raise NotImplementedError()

    def multi_source_dijkstra(self, sources: Set[int], weight: Callable[[int, int, Requirement], float]):
        raise NotImplementedError()

    def single_source_dijkstra_path(self, source: int):
        raise NotImplementedError()

    def strongly_connected_components(self) -> Iterator[Set[int]]:
        raise NotImplementedError()


class RandovaniaGraph(BaseGraph):
    edges: Dict[int, Dict[int, Requirement]]

    @classmethod
    def new(cls):
        return cls({})

    def __init__(self, edges: Dict[int, Dict[int, Requirement]]):
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

    def add_edge(self, previous_node: int, next_node: int, requirement: Requirement):
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

    def multi_source_dijkstra(self, sources: Set[int], weight: Callable[[int, int, Requirement], float]):
        return networkx.multi_source_dijkstra(self, sources, weight=weight)

    def single_source_dijkstra_path(self, source: int):
        return networkx.single_source_dijkstra_path(self, source, weight="unweighted")

    def strongly_connected_components(self) -> Iterator[Set[int]]:
        yield from networkx.strongly_connected_components(self)

    # Networkx compatibility API
    def is_multigraph(self):
        return False

    def is_directed(self):
        return True

    @property
    def _succ(self):
        return self.edges

    def __iter__(self):
        yield from self.edges.keys()

    def __getitem__(self, n):
        return self.edges[n].keys()
