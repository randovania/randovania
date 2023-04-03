import contextlib
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import MemoryOperationException
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="backend")
def dolphin_backend():
    prime_con_builder = MagicMock(PrimeConnectorBuilder)
    backend = ConnectionBackend(prime_con_builder)
    backend.connector = MagicMock(PrimeRemoteConnector)
    backend.connector.executor = MagicMock(DolphinExecutor)
    return backend


@pytest.mark.parametrize("failure_at", [None, 1, 2])
@pytest.mark.parametrize("depth", [0, 1, 2])
async def test_interact_with_game(backend: ConnectionBackend, depth: int, failure_at: int | None):
    # Setup
    backend.connector = AsyncMock()

    backend.connector.current_game_status.return_value = (
        depth <= 1,  # has pending op
        MagicMock() if depth > 0 else None,  # world
    )

    expectation = contextlib.nullcontext()
    if failure_at == 1:
        backend.connector.get_inventory.side_effect = MemoryOperationException("error at _get_inventory")
        expectation = pytest.raises(MemoryOperationException, match="error at _get_inventory")

    backend._multiworld_interaction = AsyncMock()
    if failure_at == 2:
        backend._multiworld_interaction.side_effect = MemoryOperationException("error at _check_for_collected_index")
        expectation = pytest.raises(MemoryOperationException, match="error at _check_for_collected_index")

    expected_depth = min(depth, failure_at) if failure_at is not None else depth
    if (failure_at or 999) > depth:
        expectation = contextlib.nullcontext()

    # Run
    with expectation:
        await backend._interact_with_game(1)

    # Assert
    backend.connector.current_game_status.assert_awaited_once_with()

    if expected_depth > 0:
        backend.connector.get_inventory.assert_awaited_once_with()
    else:
        backend.connector.get_inventory.assert_not_awaited()

    if expected_depth > 1:
        backend._multiworld_interaction.assert_awaited_once_with()
    else:
        backend._multiworld_interaction.assert_not_awaited()

    if 0 < depth:
        assert backend._world is not None
    else:
        assert backend._world is None


def test_current_status_disconnected(backend: ConnectionBackend):
    backend.connector.executor.is_connected.return_value = False
    assert backend.current_status == GameConnectionStatus.Disconnected


def test_current_status_unknown_game(backend: ConnectionBackend):
    backend.connector = None
    assert backend.current_status == GameConnectionStatus.UnknownGame


def test_current_status_wrong_game(backend: ConnectionBackend):
    backend.connector.executor.is_connected.return_value = True
    backend.connector.game_enum = RandovaniaGame.METROID_PRIME
    backend.set_expected_game(RandovaniaGame.METROID_PRIME_ECHOES)
    assert backend.current_status == GameConnectionStatus.WrongGame

def test_current_status_not_in_game(backend: ConnectionBackend):
    backend.connector.executor.is_connected.return_value = True
    assert backend.current_status == GameConnectionStatus.TitleScreen


def test_current_status_tracker_only(backend: ConnectionBackend):
    backend.connector.executor.is_connected.return_value = True
    backend._world = True
    assert backend.current_status == GameConnectionStatus.TrackerOnly


def test_current_status_in_game(backend: ConnectionBackend):
    backend.connector.executor.is_connected.return_value = True
    backend._world = True
    backend.checking_for_collected_index = True
    assert backend.current_status == GameConnectionStatus.InGame


@pytest.mark.parametrize("depth", [0, 1, 2])
async def test_multiworld_interaction(backend: ConnectionBackend, depth: int):
    # Setup
    # depth 0: wrong game
    # depth 1: non-empty known_collected_locations with patch
    # depth 2: empty known_collected_locations and empty receive_remote_pickups

    game_enum = RandovaniaGame.METROID_PRIME_CORRUPTION

    location_collected = AsyncMock()
    backend.set_location_collected_listener(location_collected)
    if depth > 0:
        backend.set_expected_game(game_enum)

    connector = AsyncMock()
    connector.game_enum = game_enum
    backend.connector = connector
    backend._inventory = MagicMock()
    backend._permanent_pickups = MagicMock()

    connector.receive_remote_pickups.return_value = ([], False)
    if depth == 1:
        connector.known_collected_locations.return_value = ([PickupIndex(2), PickupIndex(5)])
    else:
        connector.known_collected_locations.return_value = ([])

    # Run
    await backend._multiworld_interaction()

    # Assert
    connector.known_collected_locations.assert_has_awaits(
        [call()]
        if depth > 0 else []
    )
    if depth == 1:
        location_collected.assert_has_awaits([
            call(game_enum, PickupIndex(2)),
            call(game_enum, PickupIndex(5)),
        ])
    else:
        location_collected.assert_not_awaited()

    if depth == 2:
        connector.receive_remote_pickups.assert_awaited_once_with(
            backend._inventory, backend._permanent_pickups
        )
    else:
        connector.receive_remote_pickups.assert_not_awaited()


@pytest.mark.parametrize("depth", [0, 1, 2, 3])
async def test_update(backend: ConnectionBackend, depth: int):
    # Setup
    # depth 0: not enabled
    # depth 1: build_connector fails
    # depth 2: build_connector works but not connected
    # depth 3: connected
    executor = AsyncMock()
    executor.connect = AsyncMock(return_value=depth == 3)
    executor.disconnect = AsyncMock()

    backend._enabled = depth > 0
    if depth == 1:
        backend.connector = None
        backend.connector_builder.build_connector = AsyncMock(return_value=None)
    else:
        backend.connector.executor = executor

    backend.connector_builder.executor = executor

    # backend.connector_builder.executor.connect = AsyncMock(return_value=depth > 2)
    backend._interact_with_game = AsyncMock()

    # Run
    await backend.update(1)

    if depth == 0:
        backend.connector_builder.build_connector.assert_not_awaited()
        backend.connector_builder.executor.connect.assert_not_awaited()
    elif depth == 1:
        backend.connector_builder.build_connector.assert_awaited_once_with()
        backend.connector_builder.executor.connect.assert_not_awaited()
    elif depth == 2:
        backend.connector_builder.build_connector.assert_not_awaited()
        backend.connector_builder.executor.connect.assert_awaited_once_with()
        backend._interact_with_game.assert_not_awaited()
    elif depth == 3:
        backend.connector_builder.build_connector.assert_not_awaited()
        backend.connector_builder.executor.connect.assert_awaited_once_with()
        backend._interact_with_game.assert_awaited_once_with(1)


@pytest.mark.parametrize("connected_game", [None, RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES])
@pytest.mark.parametrize("expected_game", [None, RandovaniaGame.METROID_PRIME_ECHOES])
@pytest.mark.parametrize("interact_fails", [False, True])
async def test_update_calls_interact_with_game(backend: ConnectionBackend, interact_fails,
                                               expected_game, connected_game):
    # Setup
    executor = AsyncMock()
    executor.connect = AsyncMock(True)
    executor.disconnect = AsyncMock()
    backend._world = True
    backend.set_expected_game(expected_game)
    backend.connector.game_enum = connected_game
    backend.connector_builder.executor = executor
    if connected_game is not None:
        connector = AsyncMock()
        connector.game_enum = connected_game
        connector.executor = executor
        backend.connector = connector
    else:
        backend.connector = None
        backend.connector_builder.build_connector = AsyncMock(return_value=None)

    backend._interact_with_game = AsyncMock(side_effect=MemoryOperationException("err") if interact_fails else None)

    should_call_interact = connected_game is not None
    if should_call_interact:
        should_call_interact = (expected_game == connected_game) or (expected_game is None)

    # Run
    await backend.update(1)

    # Assert
    if should_call_interact:
        backend._interact_with_game.assert_awaited_once_with(1)
        if interact_fails:
            assert backend._world is None
        else:
            assert backend._world is not None
    else:
        backend._interact_with_game.assert_not_awaited()


def test_get_current_inventory(backend: ConnectionBackend):
    # Setup
    inventory = {"a": 5}
    backend._inventory = inventory

    # Run
    result = backend.get_current_inventory()

    # Assert
    assert result is inventory
