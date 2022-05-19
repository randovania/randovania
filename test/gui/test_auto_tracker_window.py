import pytest
from mock import MagicMock

from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.gui.auto_tracker_window import AutoTrackerWindow


@pytest.fixture(name="window")
def auto_tracker_window(skip_qtbot):
    connection = MagicMock()
    connection.pretty_current_status = "Pretty"
    window = AutoTrackerWindow(connection, MagicMock())
    skip_qtbot.addWidget(window)
    return window


def test_update_tracker_from_hook(window, echoes_resource_database):
    # Setup
    items = echoes_resource_database.item
    inventory = {
        items[i]: InventoryItem(i % 3, i % 3)
        for i in range(len(items))
    }

    # Run
    window._update_tracker_from_hook(inventory)


@pytest.mark.parametrize("current_status", [GameConnectionStatus.Disconnected,
                                            GameConnectionStatus.TrackerOnly,
                                            GameConnectionStatus.InGame])
@pytest.mark.parametrize("correct_game", [False, True])
async def test_on_timer_update(current_status: GameConnectionStatus, correct_game,
                               skip_qtbot, mocker):
    # Setup
    inventory = {}
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Pretty Status"

    window = AutoTrackerWindow(game_connection, MagicMock())
    skip_qtbot.addWidget(window)
    window._update_timer = MagicMock()
    window._update_tracker_from_hook = MagicMock()

    game_connection.get_current_inventory.return_value = inventory
    game_connection.current_status = current_status

    if correct_game:
        window._current_tracker_game = game_connection.connector.game_enum

    # Run
    await window._on_timer_update_raw()

    # Assert
    if current_status != GameConnectionStatus.Disconnected and correct_game:
        window._update_tracker_from_hook.assert_called_once_with(inventory)
    else:
        window._update_tracker_from_hook.assert_not_called()
    window._update_timer.start.assert_called_once_with()


@pytest.mark.parametrize("name", ["Metroid Prime 1 - Game Art (Standard)", "Metroid Prime 2 - Game Art (Standard)"])
def test_create_tracker(window: AutoTrackerWindow, name):
    window.create_tracker()
    assert len(window._tracker_elements) == 0
    for action, action_name in window._action_to_name.items():
        if action_name == name:
            action.setChecked(True)

    window.create_tracker()
    assert len(window._tracker_elements) > 10
