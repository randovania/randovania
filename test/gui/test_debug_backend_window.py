import pytest
from PySide2.QtCore import Qt
from mock import patch, MagicMock, AsyncMock

from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.gui.debug_backend_window import DebugBackendWindow
from randovania.interface_common.enum_lib import iterate_enum


@pytest.fixture(name="backend")
def debug_backend_window(skip_qtbot):
    return DebugBackendWindow()


@pytest.fixture(name="pickup")
def _pickup() -> PickupEntry:
    return PickupEntry(
        name="Pickup",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        broad_category=ItemCategory.LIFE_SUPPORT,
        resources=(
            ConditionalResources(None, None, ()),
        ),
    )


@pytest.mark.parametrize("expected_status", iterate_enum(ConnectionStatus))
def test_current_status(backend, expected_status):
    all_status = list(iterate_enum(ConnectionStatus))

    backend.current_status_combo.setCurrentIndex(all_status.index(expected_status))
    assert backend.current_status == expected_status


def test_display_message(backend):
    message = "Foo"
    backend.display_message(message)
    assert backend.messages_list.findItems(message, Qt.MatchFlag.MatchExactly)


@pytest.mark.asyncio
async def test_empty_get_inventory(backend):
    assert await backend.get_inventory() == {}


def test_send_pickup(backend, pickup):
    backend.send_pickup(pickup)
    assert backend.inventory_label.text() == "Pickup x1"


def test_set_permanent_pickups(backend, pickup):
    backend.set_permanent_pickups([pickup])
    assert backend.inventory_label.text() == "Pickup x1"


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

    # Run
    await backend._setup_locations_combo()

    # Assert
    mock_get_network_client.assert_called_once_with()
    assert backend.collect_location_combo.count() > 100


def test_clear(backend):
    backend.clear()
    assert backend.messages_list.count() == 0
    assert backend.inventory_label.text() == ""
