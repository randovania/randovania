from unittest.mock import MagicMock, call, patch, ANY

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import ConnectionStatus
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.games.prime import dol_patcher


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = DolphinBackend()
    backend.dolphin = MagicMock()
    return backend


def test_identify_game_ntsc(backend):
    # Setup
    backend.dolphin.read_bytes.return_value = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"

    # Run
    assert backend._identify_game()

    # Assert
    assert backend.patches is dol_patcher.ALL_VERSIONS_PATCHES[0]


def test_identify_game_error(backend):
    # Setup
    backend.dolphin.read_bytes.side_effect = RuntimeError("not connected")

    # Run
    assert not backend._identify_game()
    backend.dolphin.un_hook.assert_called_once()


def test_identify_game_already_known(backend):
    # Setup
    backend.patches = True
    backend.dolphin.read_bytes.side_effect = RuntimeError("not connected")

    # Run
    assert backend._identify_game()


@pytest.mark.asyncio
async def test_send_message(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.dolphin.read_byte.return_value = 0
    string_ref = backend.patches.string_display.message_receiver_string_ref
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    await backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend.dolphin.read_byte.assert_called_once_with(has_message_address)
    backend.dolphin.write_bytes.assert_called_once_with(string_ref, b'\x00M\x00a\x00g\x00o\x00o\x00\x00')
    backend.dolphin.write_byte.assert_called_once_with(has_message_address, 1)


@pytest.mark.asyncio
async def test_send_message_from_queue_no_messages(backend):
    await backend._send_message_from_queue(1)
    backend.dolphin.read_byte.assert_not_called()


@pytest.mark.asyncio
async def test_send_message_has_pending_message(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.dolphin.read_byte.return_value = 1
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    await backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend.dolphin.read_byte.assert_called_once_with(has_message_address)
    assert len(backend.message_queue) > 0


@pytest.mark.asyncio
async def test_send_message_on_cooldown(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.dolphin.read_byte.return_value = 0
    backend.message_cooldown = 2
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    await backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend.dolphin.read_byte.assert_called_once_with(has_message_address)
    assert len(backend.message_queue) > 0
    assert backend.message_cooldown == 1


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
    backend.LocationCollected = MagicMock()

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
    backend.LocationCollected.emit.assert_called_once_with(9)


@pytest.mark.asyncio
async def test_check_for_collected_index_receive_items(backend):
    # Setup
    pickup = MagicMock()
    resource = MagicMock()
    inventory = {resource: 10}

    backend._get_player_state_address = AsyncMock(return_value=0)
    backend.get_inventory = AsyncMock(return_value=inventory)
    backend._raw_set_item_capacity = AsyncMock()
    backend.dolphin.read_word.return_value = 0
    backend._permanent_pickups = [pickup]

    # Run
    with patch("randovania.game_connection.dolphin_backend._add_pickup_to_resources",
               autospec=True, return_value=inventory) as mock_add_pickup:
        await backend._check_for_collected_index()

    # Assert
    backend.dolphin.read_word.assert_has_calls([
        call(980),
        call(984),
    ])
    backend.dolphin.write_word.assert_called_once_with(984, 1)
    backend.get_inventory.assert_called_once_with()
    backend._raw_set_item_capacity.assert_awaited_once_with(resource.index, 10, 0)
    mock_add_pickup.assert_called_once_with(pickup, inventory)


@pytest.mark.asyncio
async def test_get_inventory(backend):
    # Setup
    backend._get_player_state_address = AsyncMock(return_value=0)
    backend.dolphin.read_word.side_effect = [
        item.index
        for item in backend.game.resource_database.item
    ]

    # Run
    inventory = await backend.get_inventory()

    # Assert
    assert inventory == {
        item: item.index
        for item in backend.game.resource_database.item
    }


@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_update(backend, depth: int):
    # Setup
    backend._ensure_hooked = MagicMock(return_value=depth == 0)
    backend._identify_game = MagicMock(return_value=depth > 1)
    backend._send_message_from_queue = AsyncMock()
    backend._update_current_world = MagicMock()
    backend._check_for_collected_index = AsyncMock()
    backend._world = MagicMock() if depth > 2 else None

    # Run
    await backend.update(1)

    # Assert
    backend._ensure_hooked.assert_called_once_with()
    backend._identify_game.assert_has_calls([call()] if depth > 0 else [])
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


def test_current_status_in_game(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    backend._world = True
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
