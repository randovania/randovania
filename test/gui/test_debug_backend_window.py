import struct

import pytest
from PySide2.QtCore import Qt
from mock import patch, MagicMock, AsyncMock

from randovania.game_connection.connection_base import InventoryItem
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation
from randovania.gui.debug_backend_window import DebugBackendWindow


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


@pytest.fixture(name="backend")
def debug_backend_window(skip_qtbot):
    return DebugBackendWindow()


@pytest.mark.asyncio
async def test_display_message(backend: DebugBackendWindow):
    connector = PrimeRemoteConnector(backend._used_version)

    message = "Foo"
    await backend.perform_single_memory_operation(connector._write_string_to_game_buffer(message))
    await backend.perform_single_memory_operation(
        MemoryOperation(backend._used_version.cstate_manager_global + 0x2, write_bytes=b"\x01"))

    backend._read_message_from_game()
    assert backend.messages_list.findItems(message, Qt.MatchFlag.MatchExactly)


@pytest.mark.asyncio
async def test_update_inventory_label(backend: DebugBackendWindow, echoes_resource_database):
    # Setup
    offset_func = _echoes_powerup_offset
    player_state_pointer = backend._used_version.cstate_manager_global + 0x150c
    item_inv = {
        echoes_resource_database.energy_tank: InventoryItem(4, 4),
        echoes_resource_database.multiworld_magic_item: InventoryItem(0, 2),
    }

    memory_ops = [
        MemoryOperation(
            address=player_state_pointer,
            offset=offset_func(item.index),
            write_bytes=struct.pack(">II", *item_inv[item])
        )
        for item in [echoes_resource_database.energy_tank, echoes_resource_database.multiworld_magic_item]
    ]
    await backend.perform_memory_operations(memory_ops)

    # Run
    await backend._update_inventory_label()

    # Assert
    assert "Energy Tank x 4/4" in backend.inventory_label.text()
    assert "Multiworld Magic Identifier x 0/2" in backend.inventory_label.text()


@pytest.mark.asyncio
@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
async def test_setup_locations_combo(mock_get_network_client: MagicMock,
                                     backend: DebugBackendWindow):
    # Setup
    patcher_data = {
        "pickups": [
            {"pickup_index": i, "hud_text": f"Item {i}"}
            for i in range(110)
        ]
    }
    mock_get_network_client.return_value.session_admin_player = AsyncMock(return_value=patcher_data)
    backend._used_version = backend._used_version

    # Run
    await backend._setup_locations_combo()

    # Assert
    mock_get_network_client.assert_called_once_with()
    assert backend.collect_location_combo.count() > 100


def test_clear(backend: DebugBackendWindow):
    backend.clear()
    assert backend.messages_list.count() == 0
    assert backend.inventory_label.text() == ""
