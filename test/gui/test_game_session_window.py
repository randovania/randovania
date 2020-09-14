import datetime

import pytest
from mock import MagicMock, AsyncMock

from randovania.gui.game_session_window import GameSessionWindow
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry, User, GameSessionAction


def test_on_game_session_updated(preset_manager, skip_qtbot):
    # Setup
    network_client = MagicMock()
    network_client.current_user = User(id=12, name="Player A")
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Maybe Connected"

    initial_session = GameSessionEntry(
        id=1234,
        name="The Session",
        num_teams=2,
        presets=[preset_manager.default_preset, preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, 0, True),
        },
        actions=[],
        seed_hash=None,
        word_hash=None,
        spoiler=None,
        in_game=False,
    )
    second_session = GameSessionEntry(
        id=1234,
        name="The Session",
        num_teams=1,
        presets=[preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, 0, True),
            24: PlayerSessionEntry(24, "Player B", 0, None, False),
        },
        actions=[
            GameSessionAction("Hello", 0, datetime.datetime(year=2020, month=1, day=5))
        ],
        seed_hash="AB12",
        word_hash="Chykka Required",
        spoiler=True,
        in_game=True,
    )
    network_client.current_game_session = initial_session

    window = GameSessionWindow(network_client, game_connection, preset_manager, MagicMock())
    window.sync_multiworld_client_status = MagicMock()

    # Run
    window.on_game_session_updated(second_session)
    window.sync_multiworld_client_status.assert_called_once_with()


@pytest.mark.parametrize("in_game", [False, True])
def test_sync_multiworld_client_status(skip_qtbot, mocker, in_game):
    # Setup
    network_client = MagicMock()
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Maybe Connected"
    mock_create_task: MagicMock = mocker.patch("asyncio.create_task")
    mocker.patch("randovania.gui.game_session_window.GameSessionWindow.on_game_session_updated")

    window = GameSessionWindow(network_client, game_connection, MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._game_session.in_game = in_game

    # Run
    window.sync_multiworld_client_status()

    # Assert
    mock_create_task.assert_called_once()
