import pytest
from mock import MagicMock

from randovania.game_connection.connection_base import GameConnectionStatus, InventoryItem
from randovania.games.game import RandovaniaGame
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
                               skip_qtbot, mocker):
    # Setup
    inventory = {}
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Pretty Status"

    mock_create_tracker: MagicMock = mocker.patch("randovania.gui.auto_tracker_window.AutoTrackerWindow.create_tracker")

    window = AutoTrackerWindow(game_connection, MagicMock())
    window._update_tracker_from_hook = MagicMock()
    mock_create_tracker.reset_mock()

    game_connection.get_current_inventory.return_value = inventory
    game_connection.current_status = current_status

    # Run
    await window._on_timer_update()

    # Assert
    if current_status != GameConnectionStatus.Disconnected:
        mock_create_tracker.assert_called_once_with(game_connection.backend.patches.game)
        window._update_tracker_from_hook.assert_called_once_with(inventory)
    else:
        mock_create_tracker.assert_not_called()
        window._update_tracker_from_hook.assert_not_called()


@pytest.mark.parametrize("game", [RandovaniaGame.PRIME1, RandovaniaGame.PRIME2])
def test_create_tracker(window: AutoTrackerWindow, game):
    window.create_tracker(game)
    assert len(window._tracker_elements) > 10
    window.create_tracker(game)
