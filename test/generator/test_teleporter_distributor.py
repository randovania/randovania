from __future__ import annotations

import random
from random import Random
from unittest.mock import MagicMock, patch

import pytest

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.generator import teleporter_distributor
from randovania.generator.teleporter_distributor import TeleporterHelper

nc = NodeIdentifier.create


@pytest.mark.parametrize(
    ("seed_number", "expected_ids"),
    [
        (
            5000,
            [
                122,
                129,
                1638535,
                393260,
                4522032,
                204865660,
                4260106,
                2097251,
                38,
                589851,
                2162826,
                1245332,
                1572998,
                1245307,
                3342446,
                524321,
                2949235,
                1966093,
                3538975,
                152,
            ],
        ),
        (
            9000,
            [
                2949235,
                129,
                152,
                4522032,
                4260106,
                1245332,
                1966093,
                122,
                1638535,
                393260,
                204865660,
                589851,
                1572998,
                38,
                2097251,
                2162826,
                3538975,
                524321,
                1245307,
                3342446,
            ],
        ),
        (
            1157772449,
            [
                393260,
                204865660,
                4522032,
                122,
                129,
                2949235,
                1638535,
                589851,
                38,
                2097251,
                4260106,
                3538975,
                3342446,
                1245332,
                1966093,
                524321,
                2162826,
                152,
                1572998,
                1245307,
            ],
        ),
    ],
)
def test_try_randomize_teleporters(seed_number: int, expected_ids: list[int], echoes_game_description):
    # Setup
    rng = Random(seed_number)
    elevator_type = echoes_game_description.dock_weakness_database.find_type("elevator")
    teleporters = [
        node.identifier
        for node in echoes_game_description.region_list.all_nodes
        if isinstance(node, DockNode)
        and (node.dock_type is elevator_type and node.extra["teleporter_instance_id"] in expected_ids)
    ]
    teleporters.sort()

    # Run
    result = teleporter_distributor.try_randomize_teleporters(
        rng,
        teleporter_distributor.create_teleporter_database(
            echoes_game_description.region_list, teleporters, [elevator_type]
        ),
    )

    def get_connected_id(teleporter: TeleporterHelper) -> str:
        assert teleporter.connected_teleporter is not None
        node = echoes_game_description.region_list.node_by_identifier(teleporter.connected_teleporter.teleporter)
        return node.extra["teleporter_instance_id"]

    connected_ids = [get_connected_id(teleporter) for teleporter in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.teleporter_distributor.try_randomize_teleporters", autospec=True)
def test_two_way_teleporter_connections_between_areas(
    mock_try_randomize_teleporters: MagicMock,
):
    # Setup
    rng = MagicMock()
    teleporter_a: TeleporterHelper = MagicMock()
    teleporter_b: TeleporterHelper = MagicMock()
    mock_try_randomize_teleporters.return_value = [teleporter_a, teleporter_b]

    # Run
    result = teleporter_distributor.two_way_teleporter_connections(rng, (teleporter_a, teleporter_b), True)

    # Assert
    mock_try_randomize_teleporters.assert_called_once_with(rng, (teleporter_a, teleporter_b))
    assert teleporter_a.connected_teleporter is not None
    assert teleporter_b.connected_teleporter is not None

    assert result == {
        teleporter_a.teleporter: teleporter_a.connected_teleporter.teleporter,
        teleporter_b.teleporter: teleporter_b.connected_teleporter.teleporter,
    }


def test_two_way_teleporter_connections_unchecked():
    # Setup
    rng = random.Random(5000)
    teleporters = [TeleporterHelper(nc(f"w{i}", f"a{i}", f"n{i}"), nc(f"w{i}", f"a{i}", f"n{i}")) for i in range(6)]
    database = tuple(teleporters)

    # Run
    result = teleporter_distributor.two_way_teleporter_connections(rng, database, False)

    # Assert
    assert result == {
        nc("w0", "a0", "n0"): nc("w4", "a4", "n4"),
        nc("w1", "a1", "n1"): nc("w2", "a2", "n2"),
        nc("w2", "a2", "n2"): nc("w1", "a1", "n1"),
        nc("w3", "a3", "n3"): nc("w5", "a5", "n5"),
        nc("w4", "a4", "n4"): nc("w0", "a0", "n0"),
        nc("w5", "a5", "n5"): nc("w3", "a3", "n3"),
    }


@pytest.mark.parametrize(
    ("replacement", "expected"),
    [
        (
            False,
            {
                nc("w0", "a0", "n0"): nc("w1", "a1", "n1"),
                nc("w1", "a1", "n1"): nc("w2", "a2", "n2"),
                nc("w2", "a2", "n2"): nc("w3", "a3", "n3"),
                nc("w3", "a3", "n3"): nc("w5", "a5", "n5"),
                nc("w4", "a4", "n4"): nc("w0", "a0", "n0"),
                nc("w5", "a5", "n5"): nc("w4", "a4", "n4"),
            },
        ),
        (
            True,
            {
                nc("w0", "a0", "n0"): nc("w2", "a2", "n2"),
                nc("w1", "a1", "n1"): nc("w3", "a3", "n3"),
                nc("w2", "a2", "n2"): nc("w4", "a4", "n4"),
                nc("w3", "a3", "n3"): nc("w2", "a2", "n2"),
                nc("w4", "a4", "n4"): nc("w5", "a5", "n5"),
                nc("w5", "a5", "n5"): nc("w3", "a3", "n3"),
            },
        ),
    ],
)
def test_one_way_teleporter_connections(echoes_game_description, replacement, expected):
    # Setup
    rng = random.Random(5000)
    target_locations = [nc(f"w{i}", f"a{i}", f"n{i}") for i in range(6)]
    teleporters = [TeleporterHelper(nc(f"w{i}", f"a{i}", f"n{i}"), nc(f"w{i}", f"a{i}", f"n{i}")) for i in range(6)]
    database = tuple(teleporters)

    # Run
    result = teleporter_distributor.one_way_teleporter_connections(rng, database, target_locations, replacement)

    # Assert
    assert result == expected
