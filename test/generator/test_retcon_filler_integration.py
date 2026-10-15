from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock

import pytest

import randovania.generator.filler.player_state
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.graph.world_graph import WorldGraph, WorldGraphNode


@pytest.mark.parametrize("single_group", [False, True])
@pytest.mark.parametrize("has_exclusion", [False, True])
def test_build_available_indices(has_exclusion: bool, default_filler_config, single_group):
    # Setup
    region_a = MagicMock(spec=Region)
    region_a.name = "A"

    region_b = MagicMock(spec=Region)
    region_b.name = "B"

    def make_pickup(region, i: int) -> MagicMock:
        result = MagicMock(spec=PickupNode)
        result.pickup_index = PickupIndex(i)
        result.custom_index_group = "G" if single_group else None

        graph_node = MagicMock(spec=WorldGraphNode)
        graph_node.region = region
        graph_node.area = None
        graph_node.database_node = result
        graph_node.pickup_index = result.pickup_index
        return graph_node

    graph = MagicMock(spec=WorldGraph)
    graph.nodes = [
        make_pickup(region_a, 1),
        make_pickup(region_a, 2),
        make_pickup(region_b, 3),
        make_pickup(region_b, 4),
    ]

    if has_exclusion:
        exclusion = frozenset([PickupIndex(3)])
    else:
        exclusion = frozenset()
    configuration = dataclasses.replace(default_filler_config, indices_to_exclude=exclusion)

    # Run
    indices_per_world, all_indices = randovania.generator.filler.player_state.build_available_indices(
        graph, configuration
    )

    # Assert
    a_pickups = {PickupIndex(1), PickupIndex(2)}
    b_pickups = {PickupIndex(3), PickupIndex(4)}

    if has_exclusion:
        b_pickups.remove(PickupIndex(3))

    if single_group:
        assert indices_per_world == [all_indices]
    else:
        assert indices_per_world == [a_pickups, b_pickups]
    assert all_indices == a_pickups | b_pickups
