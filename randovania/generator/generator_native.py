# distutils: language=c++
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterable

    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.generator.old_generator_reach import GraphData
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython


if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.cpython.ref import PyObject
        from cython.cimports.libcpp.utility import pair
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,
        )
        from cython.cimports.randovania.graph.graph_requirement import GraphRequirementSet, GraphRequirementSetRef
        from cython.cimports.randovania.graph.world_graph import BaseWorldGraphNode
        from cython.cimports.randovania.lib.bitmask import Bitmask
        from cython.cimports.randovania.lib.cython_helper import IndexQueue as deque
        from cython.cimports.randovania.lib.cython_helper import pvector
else:
    from randovania.generator.generator_native_helper import DistancesMapping, SearchHeapEntry
    from randovania.generator.generator_native_helper import MinPriorityQueue as min_priority_queue
    from randovania.graph.graph_requirement import (
        GraphRequirementSet,
        GraphRequirementSetRef,
    )
    from randovania.graph.world_graph import BaseWorldGraphNode
    from randovania.lib.cython_helper import Deque as deque
    from randovania.lib.cython_helper import Pair as pair
    from randovania.lib.cython_helper import Vector as vector

    pvector = vector

    class GeneratorScratch:  # unused; exists only for mypy
        is_collected: vector[int]
        seen: vector[int]
        reach_touched: vector[int]
        preorder: vector[int]
        lowlink: vector[int]
        scc_found: vector[bool]
        neighbors_vec: vector[int]
        scc_touched: vector[int]
        queue: vector[int]
        scc_queue: vector[int]

        def ensure_capacity(self, num_nodes: int) -> None:
            raise NotImplementedError

        def reset_reach(self) -> None:
            raise NotImplementedError

        def reset_scc(self) -> None:
            raise NotImplementedError

    if typing.TYPE_CHECKING:
        from randovania.game_description.resources.resource_collection import ResourceCollection
        from randovania.graph.world_graph import WorldGraph
        from randovania.lib.bitmask import Bitmask

    PyObject = object


if cython.compiled:

    @cython.final
    @cython.cclass
    class GeneratorScratch:  # type: ignore[no-redef]
        """Scratch buffers for calculate_reachable_costs/strongly_connected_components, shared
        (not copied) across GeneratorDiGraph.copy() since only one copy is ever active at a time.
        Sized once to num_nodes; touched-index lists let reset methods avoid touching every slot."""

        is_collected: pvector[cython.int]
        seen: pvector[cython.int]
        reach_touched: pvector[cython.int]

        preorder: pvector[cython.int]
        lowlink: pvector[cython.int]
        scc_found: pvector[cython.bint]
        neighbors_vec: pvector[cython.int]
        scc_touched: pvector[cython.int]
        queue: pvector[cython.int]
        scc_queue: pvector[cython.int]

        capacity: cython.size_t

        def __init__(self) -> None:
            self.capacity = 0

        @cython.cfunc
        def ensure_capacity(self, num_nodes: cython.size_t) -> cython.void:
            if self.capacity < num_nodes:
                self.is_collected.assign(num_nodes, 2)
                self.seen.assign(num_nodes, 1 << 30)
                self.preorder.assign(num_nodes, -1)
                self.lowlink.assign(num_nodes, 1000000)
                self.scc_found.assign(num_nodes, False)
                self.neighbors_vec.assign(num_nodes, 0)
                self.capacity = num_nodes

        @cython.cfunc
        def reset_reach(self) -> cython.void:
            idx: cython.int
            for idx in self.reach_touched:
                self.is_collected[idx] = 2
                self.seen[idx] = 1 << 30
            self.reach_touched.clear()

        @cython.cfunc
        def reset_scc(self) -> cython.void:
            idx: cython.int
            for idx in self.scc_touched:
                self.preorder[idx] = -1
                self.lowlink[idx] = 1000000
                self.scc_found[idx] = False
                self.neighbors_vec[idx] = 0
            self.scc_touched.clear()
            self.queue.clear()
            self.scc_queue.clear()

    @cython.final
    @cython.cclass
    class GeneratorDiGraph:
        # Dense (not hash-set) so `copy()`'s assignment is a memcpy instead of a full rehash-copy.
        _added_nodes: pvector[cython.int]
        _edges: pvector[pvector[pair[cython.int, GraphRequirementSetRef]]]
        # Shared (not copied) across copy(): only one copy is ever active at a time, so the scratch
        # buffers used by calculate_reachable_costs/strongly_connected_components can be reused.
        _scratch: GeneratorScratch | None

        def __init__(self) -> None:
            raise TypeError("normal construction not allowed")

        @staticmethod
        def new(game: WorldGraph) -> GeneratorDiGraph:
            num_nodes: cython.int = len(game.nodes)

            result: GeneratorDiGraph = GeneratorDiGraph.__new__(GeneratorDiGraph)
            result._edges.resize(num_nodes, pvector[pair[cython.int, GraphRequirementSetRef]]())
            result._added_nodes.resize(num_nodes, 0)
            result._scratch = None

            return result

        @cython.ccall
        def copy(self) -> GeneratorDiGraph:
            result: GeneratorDiGraph = GeneratorDiGraph.__new__(GeneratorDiGraph)
            result._added_nodes = self._added_nodes
            result._edges = self._edges
            result._scratch = self._scratch
            return result

        @cython.cfunc
        def _get_scratch(self, num_nodes: cython.int) -> GeneratorScratch:
            if self._scratch is None:
                self._scratch = GeneratorScratch()
            self._scratch.ensure_capacity(num_nodes)
            return self._scratch

        @cython.ccall
        def add_node(self, node: cython.int) -> cython.void:
            self._added_nodes[node] = 1

        @cython.ccall
        def has_node(self, node: cython.int) -> cython.bint:
            return self._added_nodes[node] != 0

        @cython.ccall
        def add_edge(self, previous_node: cython.int, next_node: cython.int, data: GraphData) -> cython.void:
            self._edges[previous_node].push_back(
                pair[cython.int, GraphRequirementSetRef](next_node, GraphRequirementSetRef(data))
            )

        @cython.ccall
        def remove_edge(self, previous_node: cython.int, next_node: cython.int) -> cython.void:
            idx: cython.int
            for idx in range(self._edges[previous_node].size()):
                if self._edges[previous_node][idx].first == next_node:
                    self._edges[previous_node].erase(self._edges[previous_node].begin() + idx)
                    return  # type: ignore[return-value]
            raise ValueError("Edge not found")

        @cython.ccall
        def has_edge(self, previous_node: cython.int, next_node: cython.int) -> cython.bint:
            for entry in self._edges[previous_node]:
                if entry.first == next_node:
                    return True
            return False

        def get_edge_data(self, previous_node: cython.int, next_node: cython.int) -> GraphData | None:
            for entry in self._edges[previous_node]:
                if entry.first == next_node:
                    return entry.second.get()
            return None

        def strongly_connected_components(self, target_node: cython.int) -> set[cython.int]:
            """Finds the strongly connected component with the given node"""

            # Uses the Tarjan's algorithm, stolen from networkx

            num_nodes: cython.int = cython.cast(cython.int, self._edges.size())
            scratch: GeneratorScratch = self._get_scratch(num_nodes)
            try:
                scratch.queue.clear()
                scratch.scc_queue.clear()

                i: cython.int = 0  # Preorder counter
                w: cython.int
                source: cython.int

                for source in range(num_nodes):
                    if not self._added_nodes[source]:
                        continue
                    if not scratch.scc_found[source]:
                        scratch.queue.push_back(source)
                        while not scratch.queue.empty():
                            v: cython.int = scratch.queue.back()
                            if scratch.preorder[v] == -1:
                                i = i + 1
                                scratch.preorder[v] = i
                                scratch.scc_touched.push_back(v)

                            done: cython.bint = True
                            while scratch.neighbors_vec[v] < self._edges[v].size():
                                w = self._edges[v][scratch.neighbors_vec[v]].first
                                scratch.neighbors_vec[v] += 1

                                if scratch.preorder[w] == -1:
                                    scratch.queue.push_back(w)
                                    done = False
                                    break

                            if done:
                                scratch.lowlink[v] = scratch.preorder[v]
                                for entry in self._edges[v]:
                                    w = entry.first
                                    if not scratch.scc_found[w]:
                                        if scratch.preorder[w] > scratch.preorder[v]:
                                            scratch.lowlink[v] = min(scratch.lowlink[v], scratch.lowlink[w])
                                        else:
                                            scratch.lowlink[v] = min(scratch.lowlink[v], scratch.preorder[w])
                                scratch.queue.pop_back()
                                if scratch.lowlink[v] == scratch.preorder[v]:
                                    scc: vector[cython.int] = vector[cython.int]()
                                    scc.push_back(v)
                                    while not scratch.scc_queue.empty() and (
                                        scratch.preorder[scratch.scc_queue.back()] > scratch.preorder[v]
                                    ):
                                        k = scratch.scc_queue.back()
                                        scratch.scc_queue.pop_back()
                                        scc.push_back(k)
                                        scratch.scc_found[k] = True
                                    scratch.scc_found[v] = True
                                    if scratch.scc_found[target_node]:
                                        return set(scc)
                                else:
                                    scratch.scc_queue.push_back(v)
                raise ValueError("SCC not found")
            finally:
                scratch.reset_scc()

        def calculate_reachable_costs(
            self,
            world_graph: WorldGraph,
            state: State,
        ) -> DistancesMapping:
            """Calculate the reachable costs for GeneratorReach."""
            resources: ResourceCollection = state.resources
            resource_bitmask: Bitmask = resources.resource_bitmask
            nodes: list[BaseWorldGraphNode] = cython.cast(list[BaseWorldGraphNode], world_graph.nodes)
            num_nodes: cython.int = len(nodes)

            scratch: GeneratorScratch = self._get_scratch(num_nodes)
            try:
                source: cython.int = state.node.node_index

                dist: _DistancesDict = _DistancesDict.create(num_nodes)

                # fringe is heapq with 3-tuples (distance,c,node)
                # use the count c to avoid comparing nodes (may not be able to)
                c: cython.int = 0

                fringe_c: min_priority_queue[SearchHeapEntry] = min_priority_queue[SearchHeapEntry]()

                scratch.seen[source] = 0
                scratch.reach_touched.push_back(source)
                fringe_c.push(SearchHeapEntry(0, c, source))

                while not fringe_c.empty():
                    entry: SearchHeapEntry = fringe_c.top()
                    fringe_c.pop()

                    if dist.dists[entry.node] != -1:
                        continue  # already searched this node.

                    if entry.node != source:
                        dist.set(entry.node, entry.cost)

                    u: cython.int
                    for edge in self._edges[entry.node]:
                        u = edge.first

                        # Weight function, embedded
                        cost: cython.int = scratch.is_collected[u]
                        if cost == 2:
                            cost = not cython.cast(BaseWorldGraphNode, nodes[u]).resource_gain_bitmask.is_subset_of(
                                resource_bitmask
                            )
                            scratch.is_collected[u] = cost
                            scratch.reach_touched.push_back(u)

                        vu_dist: cython.int = entry.cost + cost
                        if dist.dists[u] != -1:
                            u_dist: cython.int = dist.dists[u]
                            if vu_dist < u_dist:
                                raise ValueError("Contradictory paths found:", "negative weights?")
                        elif vu_dist < scratch.seen[u]:
                            scratch.seen[u] = vu_dist
                            scratch.reach_touched.push_back(u)
                            c += 1
                            fringe_c.push(SearchHeapEntry(vu_dist, c, u))

                # The optional predecessor and path dictionaries can be accessed
                # by the caller via the pred and paths objects passed as arguments.
                return dist
            finally:
                scratch.reset_reach()

else:
    import rustworkx

    class GeneratorDiGraphFallback:
        graph: rustworkx.PyDiGraph
        _added_nodes: set[int]

        @classmethod
        def new(cls, game: WorldGraph) -> typing.Self:
            g = rustworkx.PyDiGraph()
            num_nodes = len(game.nodes)

            # rustworkx methods returns indices of the internal node list, instead of the data we passed
            # when creating the nodes. Instead of having to convert these indices, we'll instead just create
            # all possible nodes at once to guarantee the indices will always match.
            g.add_nodes_from(list(range(num_nodes)))
            return cls(g, set())

        def __init__(self, graph: rustworkx.PyDiGraph, added_nodes: set[int]):
            self.graph = graph
            self._added_nodes = added_nodes

        def copy(self) -> GeneratorDiGraphFallback:
            return GeneratorDiGraphFallback(self.graph.copy(), self._added_nodes.copy())

        def add_node(self, node: int) -> None:
            # Since `_graph` has all nodes always, we track added nodes separately just for the `__contains__` method.
            self._added_nodes.add(node)

        def add_edge(self, previous_node: int, next_node: int, data: GraphData) -> None:
            self.graph.add_edge(previous_node, next_node, (previous_node, next_node, data))

        def remove_edge(self, previous_node: int, next_node: int) -> None:
            self.graph.remove_edge(previous_node, next_node)

        def has_node(self, item: int) -> bool:
            return item in self._added_nodes

        def has_edge(self, previous_node: int, next_node: int) -> bool:
            return self.graph.has_edge(previous_node, next_node)

        def get_edge_data(self, previous_node: int, next_node: int) -> GraphData | None:
            if self.graph.has_edge(previous_node, next_node):
                return self.graph.get_edge_data(previous_node, next_node)[2]
            else:
                return None

        def calculate_reachable_costs(
            self,
            world_graph: WorldGraph,
            state: State,
        ) -> DistancesMapping:
            resources: ResourceCollection = state.resources
            nodes: list[WorldGraphNode] = world_graph.nodes

            is_collected: vector[cython.int] = vector[cython.int]()
            is_collected.resize(len(nodes), 2)

            def weight(data: tuple[int, int, GraphData]) -> int:
                node_index: cython.int = data[1]
                result: cython.int = is_collected[node_index]
                if result == 2:
                    result = not nodes[node_index].resource_gain_bitmask.is_subset_of(resources.resource_bitmask)
                    is_collected[node_index] = result

                return result

            return rustworkx.dijkstra_shortest_path_lengths(
                self.graph,
                state.node.node_index,
                edge_cost_fn=weight,
            )

        def strongly_connected_components(self, target_node: int) -> set[int]:
            # Since we added every possible node already, this function returns a
            # bunch of additional components with just 1 array
            # All this does is make `_calculate_safe_nodes` slower.

            for component in rustworkx.strongly_connected_components(self.graph):
                if target_node in component:
                    return set(component)

            raise ValueError("SCC not found")

    GeneratorDiGraph = GeneratorDiGraphFallback  # type: ignore[misc, assignment]


class _NativeGraphPathDef(typing.NamedTuple):
    previous_node: cython.int
    node: cython.int
    requirement: GraphRequirementSet | cython.pointer[PyObject]


if cython.compiled:
    _NativeGraphPath = cython.struct(
        previous_node=cython.int,
        node=cython.int,
        requirement=cython.pointer[PyObject],
    )

    @cython.cfunc
    def _get_requirement_from_path(path: _NativeGraphPath) -> GraphRequirementSet:  # type: ignore[valid-type]
        return cython.cast(GraphRequirementSet, path.requirement)  # type: ignore[attr-defined]

else:
    _NativeGraphPath = _NativeGraphPathDef

    def _get_requirement_from_path(path: _NativeGraphPathDef) -> GraphRequirementSet:
        return path.requirement  # type: ignore[return-value]


def generator_reach_expand_graph(
    state: State,
    world_graph: WorldGraph,
    digraph: GeneratorDiGraph,
    unreachable_paths: dict[tuple[int, int], GraphRequirementSet],
    uncollectable_nodes: dict[int, GraphRequirementSet],
    *,
    for_initial_state: cython.bint,
    possible_edges: set[tuple[cython.int, cython.int]],
) -> None:
    # print("!! _expand_graph", len(paths_to_check))

    health: cython.float = state.health_for_damage_requirements
    resources = state.resources
    all_nodes = world_graph.nodes

    paths_to_check: deque[_NativeGraphPath] = deque[_NativeGraphPath]()  # type: ignore[valid-type]
    resource_nodes_to_check: set[cython.int] = set()

    previous_node: cython.int
    requirement: GraphRequirementSet

    if for_initial_state:
        requirement = GraphRequirementSet.trivial()
        paths_to_check.push_back(
            _NativeGraphPath(
                -1,
                state.node.node_index,
                cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
            )
        )

    # Check if we can expand the corners of our graph
    for edge in possible_edges:
        edge_requirement = unreachable_paths.get(edge)
        if edge_requirement is not None and edge_requirement.satisfied(resources, health):
            paths_to_check.push_back(
                _NativeGraphPath(
                    edge[0],
                    edge[1],
                    cython.cast(cython.pointer[PyObject], edge_requirement) if cython.compiled else edge_requirement,
                )
            )
            del unreachable_paths[edge]

    while not paths_to_check.empty():
        path = paths_to_check[0]
        paths_to_check.pop_front()

        previous_node = path.previous_node  # type: ignore[attr-defined]
        current_node_index: cython.int = path.node  # type: ignore[attr-defined]

        if previous_node >= 0 and digraph.has_edge(previous_node, current_node_index):
            continue

        digraph.add_node(current_node_index)
        if previous_node >= 0:
            digraph.add_edge(previous_node, current_node_index, data=_get_requirement_from_path(path))

        node: BaseWorldGraphNode = all_nodes[current_node_index]
        if not node.resource_gain_bitmask.is_empty():
            resource_nodes_to_check.add(current_node_index)

        for connection in node.connections:
            target_node_index: cython.int = connection.target
            requirement = connection.requirement_with_self_dangerous

            if digraph.has_edge(current_node_index, target_node_index):
                continue

            if requirement.satisfied(resources, health):
                # print("* Queue path to", target_node.full_name())
                paths_to_check.push_back(
                    _NativeGraphPath(
                        current_node_index,
                        target_node_index,
                        cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
                    )
                )
            else:
                unreachable_paths[current_node_index, target_node_index] = requirement
        # print("> done")

    for node_index in sorted(resource_nodes_to_check):
        requirement = all_nodes[node_index].requirement_to_collect
        if not requirement.satisfied(resources, health):
            uncollectable_nodes[node_index] = requirement


@cython.final
@cython.cclass
class _DistancesDict:
    """A python object that keeps the results for Reachable Costs, but avoids converting to python"""

    # Dense, sentinel (-1) instead of a hash map: one pool allocation instead of one per visited node.
    dists: pvector[cython.int]
    order: vector[cython.int]

    @staticmethod
    @cython.cfunc
    def create(num_nodes: cython.int) -> _DistancesDict:
        result: _DistancesDict = _DistancesDict.__new__(_DistancesDict)
        result.dists.assign(num_nodes, -1)
        return result

    def keys(self) -> Iterable[int]:
        return sorted(self.order)

    @cython.cfunc
    def set(self, key: cython.int, value: cython.int) -> cython.void:
        self.order.push_back(key)
        self.dists[key] = value

    def __getitem__(self, item: cython.int) -> cython.int:
        return self.dists[item]

    def __contains__(self, item: cython.int) -> cython.bint:
        if item < 0 or item >= cython.cast(cython.int, self.dists.size()):
            return False
        return self.dists[item] != -1
