from unittest.mock import MagicMock

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import ConnectionStatus
from randovania.gui.auto_tracker_window import AutoTrackerWindow


@pytest.fixture(name="window")
def auto_tracker_window(skip_qtbot):
    return AutoTrackerWindow(MagicMock())


def test_update_tracker_from_hook(window):
    # Setup
    inventory = {
        item: item.index % 3
        for item in window.game_data.resource_database.item
    }

    # Run
    window._update_tracker_from_hook(inventory)


@pytest.mark.parametrize("is_in_game", [False, True])
@pytest.mark.asyncio
async def test_on_timer_update(is_in_game: bool,
                               window):
    # Setup
    inventory = {}
    game_connection = MagicMock()

    window = AutoTrackerWindow(game_connection)
    window._update_tracker_from_hook = MagicMock()

    game_connection.get_inventory = AsyncMock(return_value=inventory)
    game_connection.current_status = ConnectionStatus.InGame if is_in_game else ConnectionStatus.Disconnected

    # Run
    await window._on_timer_update()

    # Assert
    if is_in_game:
        window._update_tracker_from_hook.assert_called_once_with(inventory)
    else:
        window._update_tracker_from_hook.assert_not_called()
