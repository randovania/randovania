import pytest
from PySide2.QtCore import Qt
from mock import patch, MagicMock, AsyncMock

from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.games.prime import dol_patcher
from randovania.gui.debug_backend_window import DebugBackendWindow
from randovania.interface_common.enum_lib import iterate_enum


@pytest.fixture(name="backend")
def debug_backend_window(skip_qtbot):
    return DebugBackendWindow()


@pytest.fixture(name="pickup")
def _pickup(echoes_game_description) -> PickupEntry:
    resource = echoes_game_description.resource_database.energy_tank

    return PickupEntry(
        name="Pickup",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        broad_category=ItemCategory.LIFE_SUPPORT,
        resources=(
            ConditionalResources(None, None, ((resource, 2),)),
        ),
    )


@pytest.mark.parametrize("expected_status", iterate_enum(GameConnectionStatus))
def test_current_status(backend, expected_status):
    all_status = list(iterate_enum(GameConnectionStatus))

    backend.current_status_combo.setCurrentIndex(all_status.index(expected_status))
    assert backend.current_status == expected_status


@pytest.mark.asyncio
async def test_display_message(backend):
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]

    message = "Foo"
    await backend._perform_single_memory_operations(backend._write_string_to_game_buffer(message))
    backend._write_memory(backend.patches.cstate_manager_global + 0x2, b"\x01")
    await backend.update(1)
    assert backend.messages_list.findItems(message, Qt.MatchFlag.MatchExactly)


@pytest.mark.asyncio
async def test_update_inventory_label(backend, echoes_resource_database):
    backend._inventory = {
        echoes_resource_database.energy_tank: InventoryItem(4, 4),
        echoes_resource_database.multiworld_magic_item: InventoryItem(0, 2),
    }
    backend._update_inventory_label()
    assert "Energy Tank x 4/4" in backend.inventory_label.text()
    assert "Multiworld Magic Identifier x 0/2" in backend.inventory_label.text()


@pytest.mark.asyncio
@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
async def test_setup_locations_combo(mock_get_network_client: MagicMock,
                                     backend):
    # Setup
    patcher_data = {
        "pickups": [
            {"pickup_index": i, "hud_text": f"Item {i}"}
            for i in range(110)
        ]
    }
    mock_get_network_client.return_value.session_admin_player = AsyncMock(return_value=patcher_data)
    backend.patches = backend._expected_patches

    # Run
    await backend._setup_locations_combo()

    # Assert
    mock_get_network_client.assert_called_once_with()
    assert backend.collect_location_combo.count() > 100


def test_clear(backend):
    backend.clear()
    assert backend.messages_list.count() == 0
    assert backend.inventory_label.text() == ""
