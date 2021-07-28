import contextlib
from typing import Optional, List

import pytest
from mock import AsyncMock, MagicMock, call

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperationExecutor
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime import echoes_dol_versions


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = ConnectionBackend(MagicMock(spec=MemoryOperationExecutor))
    return backend


@pytest.mark.asyncio
async def test_identify_game_ntsc(backend: ConnectionBackend):
    # Setup
    def side_effect(ops: List[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}

    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    backend.executor.perform_memory_operations.side_effect = side_effect
    backend.executor.perform_single_memory_operation.return_value = build_info

    # Run
    connector = await backend._identify_game()

    # Assert
    assert isinstance(connector, EchoesRemoteConnector)
    assert connector.version is echoes_dol_versions.ALL_VERSIONS[0]


@pytest.mark.asyncio
async def test_identify_game_error(backend: ConnectionBackend):
    # Setup
    backend.executor.perform_memory_operations.side_effect = RuntimeError("not connected")

    # Run
    assert not await backend._identify_game()


@pytest.mark.asyncio
async def test_identify_game_already_known(backend: ConnectionBackend):
    # Setup
    backend.connector = True
    backend.executor.perform_memory_operations.side_effect = RuntimeError("not connected")
    backend.executor.perform_single_memory_operation.return_value = RuntimeError("not connected")

    # Run
    connector = await backend._identify_game()

    # Assert
    assert connector is None


@pytest.mark.parametrize("failure_at", [None, 1, 2])
@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_interact_with_game(backend: ConnectionBackend, depth: int, failure_at: Optional[int]):
    # Setup
    backend.message_cooldown = 2
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
    assert backend.message_cooldown == (2 if expected_depth < 2 else 1)
    backend.connector.current_game_status.assert_awaited_once_with(backend.executor)

    if expected_depth > 0:
        backend.connector.get_inventory.assert_awaited_once_with(backend.executor)
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
    backend.executor.is_connected.return_value = False
    assert backend.current_status == GameConnectionStatus.Disconnected


def test_current_status_unknown_game(backend: ConnectionBackend):
    backend.executor.is_connected.return_value = True
    assert backend.current_status == GameConnectionStatus.UnknownGame


def test_current_status_wrong_game(backend: ConnectionBackend):
    backend.executor.is_connected.return_value = True
    backend.connector = MagicMock()
    backend.connector.game_enum = RandovaniaGame.METROID_PRIME
    backend.set_expected_game(RandovaniaGame.METROID_PRIME_ECHOES)
    assert backend.current_status == GameConnectionStatus.WrongGame


def test_current_status_not_in_game(backend: ConnectionBackend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    assert backend.current_status == GameConnectionStatus.TitleScreen


def test_current_status_tracker_only(backend: ConnectionBackend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    backend._world = True
    assert backend.current_status == GameConnectionStatus.TrackerOnly


def test_current_status_in_game(backend: ConnectionBackend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    backend._world = True
    backend.checking_for_collected_index = True
    assert backend.current_status == GameConnectionStatus.InGame


@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_multiworld_interaction(backend: ConnectionBackend, depth: int):
    # Setup
    # depth 0: wrong game
    # depth 1: non-empty known_collected_locations with patch
    # depth 2: empty known_collected_locations and empty find_missing_remote_pickups

    game_enum = RandovaniaGame.METROID_PRIME_CORRUPTION
    patches = [MagicMock()]

    location_collected = AsyncMock()
    backend.set_location_collected_listener(location_collected)
    if depth > 0:
        backend.set_expected_game(game_enum)

    connector = AsyncMock()
    connector.game_enum = game_enum
    backend.connector = connector
    backend._inventory = MagicMock()
    backend._permanent_pickups = MagicMock()

    connector.find_missing_remote_pickups.return_value = ([], False)
    if depth == 1:
        connector.known_collected_locations.return_value = ([PickupIndex(2), PickupIndex(5)], patches)
    else:
        connector.known_collected_locations.return_value = ([], [])

    # Run
    await backend._multiworld_interaction()

    # Assert
    connector.known_collected_locations.assert_has_awaits(
        [call(backend.executor)]
        if depth > 0 else []
    )
    if depth == 1:
        location_collected.assert_has_awaits([
            call(game_enum, PickupIndex(2)),
            call(game_enum, PickupIndex(5)),
        ])
        connector.execute_remote_patches(backend.executor, patches)
    else:
        location_collected.assert_not_awaited()
        connector.execute_remote_patches.assert_not_awaited()

    if depth == 2:
        connector.find_missing_remote_pickups.assert_awaited_once_with(
            backend.executor, backend._inventory, backend._permanent_pickups, False
        )
    else:
        connector.find_missing_remote_pickups.assert_not_awaited()


@pytest.mark.parametrize("has_message", [False, True])
@pytest.mark.parametrize("has_cooldown", [False, True])
@pytest.mark.parametrize("has_patches", [False, True])
@pytest.mark.asyncio
async def test_multiworld_interaction_missing_remote_pickups(backend: ConnectionBackend, has_message: bool,
                                                             has_cooldown: bool, has_patches: bool):
    # Setup
    if has_cooldown:
        initial_cooldown = 2.0
    else:
        initial_cooldown = 0.0
    backend.message_cooldown = initial_cooldown

    game_enum = RandovaniaGame.METROID_PRIME_CORRUPTION
    backend.set_expected_game(game_enum)
    patches = [MagicMock()]

    connector = AsyncMock()
    connector.game_enum = game_enum
    backend.connector = connector
    backend._inventory = MagicMock()
    backend._permanent_pickups = MagicMock()

    connector.known_collected_locations.return_value = ([], [])
    connector.find_missing_remote_pickups.return_value = (patches if has_patches else [], has_message)

    # Run
    await backend._multiworld_interaction()

    # Assert
    if has_patches and not (has_cooldown and has_message):
        connector.execute_remote_patches.assert_awaited_once_with(backend.executor, patches)
        if has_message:
            assert backend.message_cooldown == 4.0
        else:
            assert backend.message_cooldown == initial_cooldown
    else:
        connector.execute_remote_patches.assert_not_awaited()
        assert backend.message_cooldown == initial_cooldown


@pytest.mark.parametrize("depth", [0, 1, 2, 3])
@pytest.mark.asyncio
async def test_update(backend: ConnectionBackend, depth: int):
    # Setup
    # depth 0: not enabled
    # depth 1: can't connect
    # depth 2: call identify game
    # depth 3: don't call identify game

    connector = MagicMock()
    backend._enabled = depth > 0
    backend.executor.connect = AsyncMock(return_value=depth > 1)
    backend._expected_game = None
    backend._world = True
    backend._identify_game = AsyncMock(return_value=connector)
    backend._interact_with_game = AsyncMock()
    if depth == 3:
        backend.connector = connector

    # Run
    await backend.update(1)

    # Assert
    backend.executor.connect.assert_has_calls([call()] if depth > 0 else [])

    if depth == 2:
        backend._identify_game.assert_awaited_once_with()
        assert backend.connector == connector
    else:
        backend._identify_game.assert_not_awaited()

    if depth >= 2:
        backend._interact_with_game.assert_awaited_once_with(1)
    else:
        backend._interact_with_game.assert_not_awaited()


@pytest.mark.parametrize("connected_game", [None, RandovaniaGame.METROID_PRIME, RandovaniaGame.METROID_PRIME_ECHOES])
@pytest.mark.parametrize("expected_game", [None, RandovaniaGame.METROID_PRIME_ECHOES])
@pytest.mark.parametrize("interact_fails", [False, True])
@pytest.mark.asyncio
async def test_update_calls_interact_with_game(backend: ConnectionBackend, interact_fails,
                                               expected_game, connected_game):
    # Setup
    backend.connector = None
    backend._world = True
    backend.set_expected_game(expected_game)

    if connected_game is not None:
        connector = AsyncMock()
        connector.game_enum = connected_game
    else:
        connector = None

    backend._interact_with_game = AsyncMock(side_effect=MemoryOperationException("err") if interact_fails else None)
    backend._identify_game = AsyncMock(return_value=connector)

    should_call_interact = connected_game is not None
    if should_call_interact:
        should_call_interact = (expected_game == connected_game) or (expected_game is None)

    # Run
    await backend.update(1)

    # Assert
    backend._identify_game.assert_awaited_once_with()
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
