import random
from random import Random
from unittest.mock import patch, MagicMock

import pytest

from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.generator import elevator_distributor
from randovania.generator.elevator_distributor import ElevatorHelper


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [122, 129, 1638535, 393260, 4522032, 204865660, 4260106, 2097251, 38, 589851,
            2162826, 1245332, 1572998, 1245307, 3342446, 524321, 2949235, 1966093, 3538975, 152]),
    (9000, [2949235, 129, 152, 4522032, 4260106, 1245332, 1966093, 122, 1638535, 393260,
            204865660, 589851, 1572998, 38, 2097251, 2162826, 3538975, 524321, 1245307, 3342446]),
    (1157772449, [393260, 204865660, 4522032, 122, 129, 2949235, 1638535, 589851, 38, 2097251,
                  4260106, 3538975, 3342446, 1245332, 1966093, 524321, 2162826, 152, 1572998, 1245307])
])
def test_try_randomize_elevators(seed_number: int,
                                 expected_ids: list[int],
                                 echoes_game_description):
    # Setup
    rng = Random(seed_number)
    teleporters = [
        echoes_game_description.world_list.identifier_for_node(node)
        for world in echoes_game_description.world_list.worlds
        for area in world.areas
        for node in area.nodes
        if isinstance(node, TeleporterNode) and node.editable and node.extra["teleporter_instance_id"] in expected_ids
    ]
    teleporters.sort()

    # Run
    result = elevator_distributor.try_randomize_elevators(
        rng,
        elevator_distributor.create_elevator_database(echoes_game_description.world_list, teleporters))

    connected_ids = [
        echoes_game_description.world_list.node_by_identifier(elevator.connected_elevator.teleporter
                                                              ).extra["teleporter_instance_id"]
        for elevator in result
    ]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.elevator_distributor.try_randomize_elevators", autospec=True)
def test_two_way_elevator_connections_between_areas(mock_try_randomize_elevators: MagicMock,
                                                    ):
    # Setup
    rng = MagicMock()
    elevator_a: ElevatorHelper = MagicMock()
    elevator_b: ElevatorHelper = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator_a, elevator_b
    ]

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, (elevator_a, elevator_b), True)

    # Assert
    mock_try_randomize_elevators.assert_called_once_with(rng, (elevator_a, elevator_b))
    assert result == {
        elevator_a.teleporter: elevator_a.connected_elevator.area_location,
        elevator_b.teleporter: elevator_b.connected_elevator.area_location,
    }


def test_two_way_elevator_connections_unchecked():
    # Setup
    rng = random.Random(5000)
    elevators = [
        ElevatorHelper(NodeIdentifier.create(f"w{i}", f"a{i}", f"n{i}"), AreaIdentifier(f"w{i}", f"a{i}"))
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, database, False)

    # Assert
    assert result == {
        NodeIdentifier.create("w0", "a0", "n0"): AreaIdentifier("w4", "a4"),
        NodeIdentifier.create("w1", "a1", "n1"): AreaIdentifier("w2", "a2"),
        NodeIdentifier.create("w2", "a2", "n2"): AreaIdentifier("w1", "a1"),
        NodeIdentifier.create("w3", "a3", "n3"): AreaIdentifier("w5", "a5"),
        NodeIdentifier.create("w4", "a4", "n4"): AreaIdentifier("w0", "a0"),
        NodeIdentifier.create("w5", "a5", "n5"): AreaIdentifier("w3", "a3"),
    }


@pytest.mark.parametrize(["replacement", "expected"], [
    (False, {
        NodeIdentifier.create("w0", "a0", "n0"): AreaIdentifier("w1", "a1"),
        NodeIdentifier.create("w1", "a1", "n1"): AreaIdentifier("w2", "a2"),
        NodeIdentifier.create("w2", "a2", "n2"): AreaIdentifier("w3", "a3"),
        NodeIdentifier.create("w3", "a3", "n3"): AreaIdentifier("w5", "a5"),
        NodeIdentifier.create("w4", "a4", "n4"): AreaIdentifier("w0", "a0"),
        NodeIdentifier.create("w5", "a5", "n5"): AreaIdentifier("w4", "a4"),
    }),
    (True, {
        NodeIdentifier.create("w0", "a0", "n0"): AreaIdentifier("w2", "a2"),
        NodeIdentifier.create("w1", "a1", "n1"): AreaIdentifier("w3", "a3"),
        NodeIdentifier.create("w2", "a2", "n2"): AreaIdentifier("w4", "a4"),
        NodeIdentifier.create("w3", "a3", "n3"): AreaIdentifier("w2", "a2"),
        NodeIdentifier.create("w4", "a4", "n4"): AreaIdentifier("w5", "a5"),
        NodeIdentifier.create("w5", "a5", "n5"): AreaIdentifier("w3", "a3"),
    }),
])
def test_one_way_elevator_connections(echoes_game_description, replacement, expected):
    # Setup
    rng = random.Random(5000)
    target_locations = [
        AreaIdentifier(f"w{i}", f"a{i}")
        for i in range(6)
    ]
    elevators = [
        ElevatorHelper(NodeIdentifier.create(f"w{i}", f"a{i}", f"n{i}"), AreaIdentifier(f"w{i}", f"a{i}"))
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.one_way_elevator_connections(rng, database, target_locations, replacement)

    # Assert
    assert result == expected
