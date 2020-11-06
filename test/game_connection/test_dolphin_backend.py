from unittest.mock import MagicMock, call

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_connection.dolphin_backend import DolphinBackend


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = DolphinBackend()
    backend.dolphin = MagicMock()
    return backend


@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_update(backend, depth: int):
    # Setup
    backend._ensure_hooked = MagicMock(return_value=depth == 0)
    backend._identify_game = AsyncMock(return_value=depth > 1)
    backend._send_message_from_queue = AsyncMock()
    backend._update_current_world = AsyncMock()
    backend._check_for_collected_index = AsyncMock()
    backend._world = MagicMock() if depth > 2 else None

    # Run
    await backend.update(1)

    # Assert
    backend._ensure_hooked.assert_called_once_with()
    backend._identify_game.assert_has_awaits([call()] if depth > 0 else [])
    if depth > 1:
        backend._send_message_from_queue.assert_awaited_once_with(1)
        backend._update_current_world.assert_awaited_once_with()
    else:
        backend._send_message_from_queue.assert_not_awaited()
        backend._update_current_world.assert_not_awaited()

    if depth > 2:
        backend._check_for_collected_index.assert_awaited_once_with()
    else:
        backend._check_for_collected_index.assert_not_awaited()


def test_current_status_disconnected(backend):
    backend.dolphin.is_hooked.return_value = False
    assert backend.current_status == ConnectionStatus.Disconnected


def test_current_status_wrong_game(backend):
    backend.dolphin.is_hooked.return_value = True
    assert backend.current_status == ConnectionStatus.UnknownGame


def test_current_status_not_in_game(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    assert backend.current_status == ConnectionStatus.TitleScreen


def test_current_status_tracker_only(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    backend._world = True
    assert backend.current_status == ConnectionStatus.TrackerOnly


def test_current_status_in_game(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    backend._world = True
    backend.checking_for_collected_index = True
    assert backend.current_status == ConnectionStatus.InGame
