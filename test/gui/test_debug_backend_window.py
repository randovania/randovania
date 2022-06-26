from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from PySide6.QtCore import Qt

from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector, DolRemotePatch
from randovania.gui.debug_backend_window import DebugExecutorWindow
from randovania.patching.prime import all_prime_dol_patches


def _echoes_powerup_offset(item_index: int) -> int:
    powerups_offset = 0x58
    vector_data_offset = 0x4
    powerup_size = 0xc
    return (powerups_offset + vector_data_offset) + (item_index * powerup_size)


@pytest.fixture(name="executor")
def debug_executor_window(skip_qtbot):
    window = DebugExecutorWindow()
    skip_qtbot.addWidget(window.window)
    return window


async def test_display_message(executor: DebugExecutorWindow):
    # Setup
    await executor._ensure_initialized_game_memory()
    connector = PrimeRemoteConnector(executor._used_version)
    message = "Foo Bar"

    # Run
    await connector.execute_remote_patches(
        executor,
        [connector._dol_patch_for_hud_message(message)],
    )
    executor._handle_remote_execution()

    # Assert
    assert executor.messages_list.findItems(message, Qt.MatchFlag.MatchExactly)


async def test_update_inventory_label(executor: DebugExecutorWindow, echoes_resource_database):
    # Setup
    await executor._ensure_initialized_game_memory()
    connector = PrimeRemoteConnector(executor._used_version)

    await connector.execute_remote_patches(
        executor,
        [
            DolRemotePatch([], all_prime_dol_patches.increment_item_capacity_patch(
                executor._used_version.powerup_functions,
                echoes_resource_database.game_enum,
                echoes_resource_database.multiworld_magic_item.extra["item_id"],
                delta=2,
            )),
            DolRemotePatch([], all_prime_dol_patches.adjust_item_amount_and_capacity_patch(
                executor._used_version.powerup_functions,
                echoes_resource_database.game_enum,
                echoes_resource_database.energy_tank.extra["item_id"],
                delta=4,
            )),
        ],
    )
    executor._handle_remote_execution()

    # Run
    await executor._update_inventory_label()

    # Assert
    assert "Energy Tank x 4/4" in executor.inventory_label.text()
    assert "Multiworld Magic Identifier x 0/2" in executor.inventory_label.text()


@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
async def test_setup_locations_combo(mock_get_network_client: MagicMock,
                                     executor: DebugExecutorWindow):
    # Setup
    patcher_data = {
        "pickups": [
            {"pickup_index": i, "hud_text": f"Item {i}"}
            for i in range(110)
        ]
    }
    mock_get_network_client.return_value.session_admin_player = AsyncMock(return_value=patcher_data)
    executor._used_version = executor._used_version

    # Run
    await executor._setup_locations_combo()

    # Assert
    mock_get_network_client.assert_called_once_with()
    assert executor.collect_location_combo.count() > 100


def test_clear(executor: DebugExecutorWindow):
    executor.clear()
    assert executor.messages_list.count() == 0
    assert executor.inventory_label.text() == ""
