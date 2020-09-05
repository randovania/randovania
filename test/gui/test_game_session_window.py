import datetime

import pytest
from mock import MagicMock, patch

from randovania.gui.game_session_window import GameSessionWindow
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry, User, GameSessionAction


@pytest.mark.asyncio
@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
@patch("randovania.gui.lib.common_qt_lib.get_game_connection", autospec=True)
def test_on_game_session_updated(mock_get_game_connection: MagicMock,
                                 mock_get_network_client: MagicMock,
                                 preset_manager, skip_qtbot):
    # Setup
    mock_get_network_client.return_value.current_user = User(id=12, name="Player A")
    mock_get_game_connection.return_value.pretty_current_status = "Maybe Connected"

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
    window = GameSessionWindow(initial_session, preset_manager, MagicMock())

    # Run
    window.on_game_session_updated(second_session)
