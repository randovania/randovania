from unittest.mock import MagicMock, call, patch, ANY

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_base import ConnectionStatus, InventoryItem
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.games.prime import dol_patcher


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = DolphinBackend()
    backend.dolphin = MagicMock()
    return backend


@pytest.mark.asyncio
async def test_check_for_collected_index_nothing(backend):
    # Setup
    backend._get_player_state_address = AsyncMock(return_value=0)
    backend.dolphin.read_word.return_value = 0

    # Run
    await backend._check_for_collected_index()

    # Assert
    backend.dolphin.read_word.assert_has_calls([
        call(980),
        call(984),
    ])
    backend.dolphin.write_word.assert_not_called()


@pytest.mark.asyncio
async def test_check_for_collected_index_location_collected(backend):
    # Setup
    backend._get_player_state_address = AsyncMock(return_value=0)
    backend.dolphin.read_word.return_value = 10
    backend._emit_location_collected = AsyncMock()

    # Run
    await backend._check_for_collected_index()

    # Assert
    backend.dolphin.read_word.assert_has_calls([
        call(980),
        call(984),
    ])
    backend.dolphin.write_word.assert_has_calls([
        call(980, 0),
        call(984, 0),
    ])
    backend._emit_location_collected.assert_awaited_once_with(9)


@pytest.mark.asyncio
async def test_check_for_collected_index_receive_items(backend):
    # Setup
    pickup = MagicMock()
    resource = MagicMock()
    resource.max_capacity = 8
    inventory_resources = {resource: 10}

    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._get_player_state_address = AsyncMock(return_value=0)
    backend._inventory = {resource: InventoryItem(10, 10)}
    backend._raw_set_item_capacity = AsyncMock()
    backend.dolphin.read_word.return_value = 0
    backend._permanent_pickups = [pickup]

    # Run
    with patch("randovania.game_connection.dolphin_backend._add_pickup_to_resources",
               autospec=True, return_value=inventory_resources) as mock_add_pickup:
        await backend._check_for_collected_index()

    # Assert
    backend.dolphin.read_word.assert_has_calls([
        call(980),
        call(984),
    ])
    backend.dolphin.write_word.assert_called_once_with(984, 1)
    backend._raw_set_item_capacity.assert_awaited_once_with(resource.index, 8, 0)
    mock_add_pickup.assert_called_once_with(pickup, inventory_resources)


@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_update(backend, depth: int):
    # Setup
    backend._ensure_hooked = MagicMock(return_value=depth == 0)
    backend._identify_game = AsyncMock(return_value=depth > 1)
    backend._send_message_from_queue = AsyncMock()
    backend._update_current_world = MagicMock()
    backend._check_for_collected_index = AsyncMock()
    backend._world = MagicMock() if depth > 2 else None

    # Run
    await backend.update(1)

    # Assert
    backend._ensure_hooked.assert_called_once_with()
    backend._identify_game.assert_has_awaits([call()] if depth > 0 else [])
    if depth > 1:
        backend._send_message_from_queue.assert_awaited_once_with(1)
        backend._update_current_world.assert_called_once_with()
    else:
        backend._send_message_from_queue.assert_not_awaited()
        backend._update_current_world.assert_not_called()

    if depth > 2:
        backend._check_for_collected_index.assert_awaited_once_with()
    else:
        backend._check_for_collected_index.assert_not_awaited()


def test_current_status_disconnected(backend):
    backend.dolphin.is_hooked.return_value = False
    assert backend.current_status == ConnectionStatus.Disconnected


def test_current_status_wrong_game(backend):
    backend.dolphin.is_hooked.return_value = True
    assert backend.current_status == ConnectionStatus.WrongGame


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


@pytest.mark.asyncio
async def test_raw_set_item_capacity_no_change(backend):
    # Setup
    backend.dolphin.read_word.return_value = 5

    # Run
    await backend._raw_set_item_capacity(10, 5, 0)

    # Assert
    backend.dolphin.read_word.assert_called_once()
    backend.dolphin.write_word.assert_not_called()


@pytest.mark.parametrize("item", [13])
@pytest.mark.asyncio
async def test_raw_set_item_capacity_positive_change(backend, item):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.dolphin.read_word.return_value = 4

    # Run
    await backend._raw_set_item_capacity(item, 5, 0)

    # Assert
    # backend.dolphin.read_word.assert_called_once()
    backend.dolphin.write_word.assert_has_calls([
        call(ANY, 5),
        call(ANY, 5),
        call(ANY, 1),
    ])
