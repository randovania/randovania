import datetime

import pytest
from PySide2 import QtWidgets
from mock import MagicMock, AsyncMock, ANY

from randovania.gui.game_session_window import GameSessionWindow
from randovania.layout.permalink import Permalink
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry, User, GameSessionAction
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.session_state import GameSessionState


@pytest.mark.asyncio
async def test_on_game_session_updated(preset_manager, skip_qtbot):
    # Setup
    network_client = MagicMock()
    network_client.current_user = User(id=12, name="Player A")
    game_connection = MagicMock()
    game_connection.pretty_current_status = "Maybe Connected"

    initial_session = GameSessionEntry(
        id=1234,
        name="The Session",
        presets=[preset_manager.default_preset, preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, False, True),
        },
        actions=[],
        seed_hash=None,
        word_hash=None,
        spoiler=None,
        state=GameSessionState.SETUP,
        generation_in_progress=None,
    )
    second_session = GameSessionEntry(
        id=1234,
        name="The Session",
        presets=[preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, False, True),
            24: PlayerSessionEntry(24, "Player B", 0, True, False),
        },
        actions=[
            GameSessionAction("Hello", datetime.datetime(year=2020, month=1, day=5))
        ],
        seed_hash="AB12",
        word_hash="Chykka Required",
        spoiler=True,
        state=GameSessionState.IN_PROGRESS,
        generation_in_progress=None,
    )
    network_client.current_game_session = initial_session

    window = await GameSessionWindow.create_and_update(network_client, game_connection, preset_manager,
                                                       MagicMock(), MagicMock())
    window.update_multiworld_client_status = AsyncMock()

    # Run
    await window.on_game_session_updated(second_session)
    window.update_multiworld_client_status.assert_awaited()


@pytest.mark.parametrize("in_game", [False, True])
@pytest.mark.asyncio
async def test_update_multiworld_client_status(skip_qtbot, in_game):
    # Setup
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._game_session.state = GameSessionState.IN_PROGRESS if in_game else GameSessionState.SETUP
    window.multiworld_client = MagicMock()
    window.multiworld_client.is_active = not in_game
    window.multiworld_client.start = AsyncMock()
    window.multiworld_client.stop = AsyncMock()

    # Run
    await window.update_multiworld_client_status()

    # Assert
    if in_game:
        called, not_called = window.multiworld_client.start, window.multiworld_client.stop
    else:
        called, not_called = window.multiworld_client.stop, window.multiworld_client.start
    called.assert_awaited_once()
    not_called.assert_not_awaited()


@pytest.mark.asyncio
async def test_row_show_preset_summary(skip_qtbot, mocker, preset_manager):
    # Setup
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)

    row = MagicMock()
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window.rows = [row]
    window._game_session = MagicMock()
    window._game_session.presets = [preset_manager.default_preset]

    # Run
    await window._row_show_preset_summary(row)

    # Assert
    execute_dialog.assert_awaited_once()


@pytest.mark.parametrize(["has_background_process", "generation_in_progress", "seed_hash", "expected_text"], [
    (True, None, None, "Stop"),
    (False, True, None, "Abort generation"),
    (False, None, None, "Generate game"),
    (False, None, True, "Clear generated game"),
])
def test_update_background_process_button(skip_qtbot, has_background_process, generation_in_progress, seed_hash,
                                          expected_text):
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()

    window._background_thread = True if has_background_process else None
    window._game_session.generation_in_progress = generation_in_progress
    window._game_session.seed_hash = seed_hash

    # Run
    window.update_background_process_button()

    # Assert
    assert window.background_process_button.text() == expected_text


def test_sync_background_process_to_game_session_other_generation(skip_qtbot):
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._game_session.generation_in_progress = True
    window._generating_game = False

    # Run
    window.sync_background_process_to_game_session()

    # Assert
    assert window.progress_label.text().startswith("Game being generated by")


def test_sync_background_process_to_game_session_stop_background(skip_qtbot):
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._game_session.generation_in_progress = None
    window._background_thread = True
    window._generating_game = True
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_game_session()

    # Assert
    window.stop_background_process.assert_called_once_with()


def test_sync_background_process_to_game_session_nothing(skip_qtbot):
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._game_session.generation_in_progress = None
    window._background_thread = None
    window._generating_game = False
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_game_session()

    # Assert
    assert window.progress_label.text() == ""


@pytest.mark.parametrize("has_game", [False, True])
@pytest.mark.asyncio
async def test_update_logic_settings_window(skip_qtbot, mocker, has_game):
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = MagicMock()
    window._logic_settings_window = MagicMock()
    window._game_session.seed_hash = True if has_game else None

    # Run
    await window.update_logic_settings_window()

    # Assert
    if has_game:
        window._logic_settings_window.setEnabled.assert_not_called()
        window._logic_settings_window.reject.assert_called_once_with()
        execute_dialog.assert_awaited_once()
    else:
        window._logic_settings_window.setEnabled.assert_called_once()
        execute_dialog.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password(skip_qtbot, mocker):
    def set_text_value(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue("magoo")
        return QtWidgets.QDialog.Accepted

    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                  side_effect=set_text_value)
    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._admin_global_action = AsyncMock()

    # Run
    await window.change_password()

    # Assert
    execute_dialog.assert_awaited_once()
    window._admin_global_action.assert_awaited_once_with(SessionAdminGlobalAction.CHANGE_PASSWORD, "magoo")


@pytest.mark.asyncio
async def test_generate_game(skip_qtbot, mocker, preset_manager):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.simplified_patcher.generate_layout")
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=5000)

    spoiler = True
    game_session = MagicMock()
    game_session.presets = [preset_manager.default_preset, preset_manager.default_preset]

    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = game_session
    window._upload_layout_description = AsyncMock()
    window._admin_global_action = AsyncMock()

    # Run
    await window.generate_game(spoiler)

    # Assert
    mock_randint.assert_called_once_with(0, 2 ** 31)
    mock_generate_layout.assert_called_once_with(
        progress_update=ANY,
        permalink=Permalink(
            seed_number=mock_randint.return_value,
            spoiler=spoiler,
            presets={
                0: preset_manager.default_preset.get_preset(),
                1: preset_manager.default_preset.get_preset(),
            },
        ),
        options=window._options
    )
    window._upload_layout_description.assert_awaited_once_with(mock_generate_layout.return_value)


@pytest.mark.asyncio
async def test_check_dangerous_presets(skip_qtbot, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.No

    game_session = MagicMock()
    game_session.presets = [MagicMock(), MagicMock(), MagicMock()]
    game_session.presets[0].name = "Preset A"
    game_session.presets[0].dangerous_settings.return_value = ["Cake"]
    game_session.presets[1].name = "Preset B"
    game_session.presets[1].dangerous_settings.return_value = ["Bomb", "Knife"]
    game_session.presets[2].dangerous_settings.return_value = []

    window = GameSessionWindow(MagicMock(), MagicMock(), MagicMock(), MagicMock(), MagicMock())
    window._game_session = game_session

    permalink = MagicMock()
    permalink.presets = {i: preset for i, preset in enumerate(game_session.presets)}

    # Run
    result = await window._check_dangerous_presets(permalink)

    # Assert
    message = ("The following presets have settings that can cause an impossible game:\n"
               "\nRow 0 - Preset A: Cake"
               "\nRow 1 - Preset B: Bomb, Knife"
               "\n\nDo you want to continue?")
    mock_warning.assert_awaited_once_with(window, "Dangerous preset", message,
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    assert not result
