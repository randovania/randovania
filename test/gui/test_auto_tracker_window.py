from mock import MagicMock

import pytest

from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.gui.auto_tracker_window import AutoTrackerWindow


@pytest.fixture(name="window")
def auto_tracker_window(skip_qtbot):
    connection = MagicMock()
    connection.pretty_current_status = "Pretty"
    return AutoTrackerWindow(connection, MagicMock())


def test_update_tracker_from_hook(window, echoes_resource_database):
    # Setup
    inventory = {
        item: InventoryItem(item.index % 3, item.index % 3)
        for item in echoes_resource_database.item
    }

    # Run
    window._update_tracker_from_hook(inventory)


@pytest.mark.parametrize("current_status", [GameConnectionStatus.Disconnected,
                                            GameConnectionStatus.TrackerOnly,
                                            GameConnectionStatus.InGame])
@pytest.mark.asyncio
async def test_on_timer_update(current_status: GameConnectionStatus,
                               window):
    # Setup
    inventory = {}
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Pretty Status"

    window = AutoTrackerWindow(game_connection, MagicMock())
    window._update_tracker_from_hook = MagicMock()

    game_connection.get_current_inventory.return_value = inventory
    game_connection.current_status = current_status

    # Run
    await window._on_timer_update()

    # Assert
    if current_status != GameConnectionStatus.Disconnected:
        window._update_tracker_from_hook.assert_called_once_with(inventory)
    else:
        window._update_tracker_from_hook.assert_not_called()
