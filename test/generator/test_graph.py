import pytest

from randovania.game_description.requirements.base import Requirement
from randovania.generator import graph


@pytest.mark.parametrize(
    "cls",
    [
        graph.RandovaniaGraph,
        graph.RustworkXGraph,
    ],
)
def test_graph_module(cls: type[graph.BaseGraph], blank_game_description):
    g = cls.new(blank_game_description)

    g.add_node(1)
    g.add_node(5)
    g.add_node(7)
    g.add_node(8)
    g.add_edge(1, 5, Requirement.trivial())
    g.add_edge(7, 8, Requirement.trivial())

    assert g.has_edge(1, 5)

    result = list(g.edges_data())
    assert result == [
        (1, 5, Requirement.trivial()),
        (7, 8, Requirement.trivial()),
    ]

    assert g.shortest_paths_dijkstra(1, lambda a, b, c: 0) == {1: 0, 5: 0}

    components = {tuple(component) for component in g.strongly_connected_components()}
    assert {(5,), (1,), (8,), (7,)}.issubset(components)
