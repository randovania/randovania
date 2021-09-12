import contextlib
import datetime
import sys
import typing

import pytest
from PySide2 import QtWidgets
from PySide2.QtWidgets import QMessageBox
from mock import MagicMock, AsyncMock, ANY

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.gui.game_session_window import GameSessionWindow
from randovania.layout.permalink import Permalink
from randovania.network_client.game_session import GameSessionEntry, PlayerSessionEntry, User, GameSessionAction, \
    GameSessionActions, GameDetails
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.session_state import GameSessionState


@pytest.fixture(name="window")
def _window(skip_qtbot):
    game_connection = MagicMock(spec=GameConnection)
    game_connection.executor = AsyncMock()
    game_connection.lock_identifier = None
    game_connection.pretty_current_status = "Pretty Status"
    window = GameSessionWindow(MagicMock(), game_connection, MagicMock(), MagicMock(), MagicMock())
    window.connect_to_events()
    return window


@pytest.mark.asyncio
async def test_on_game_session_meta_update(preset_manager, skip_qtbot):
    # Setup
    network_client = MagicMock()
    network_client.current_user = User(id=12, name="Player A")
    network_client.session_self_update = AsyncMock()
    game_connection = MagicMock(spec=GameConnection)
    game_connection.executor = AsyncMock()
    game_connection.pretty_current_status = "Maybe Connected"
    game_connection.lock_identifier = None

    initial_session = GameSessionEntry(
        id=1234,
        name="The Session",
        presets=[preset_manager.default_preset, preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, True, "Online"),
        },
        game_details=None,
        state=GameSessionState.SETUP,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
    )
    second_session = GameSessionEntry(
        id=1234,
        name="The Session",
        presets=[preset_manager.default_preset],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, True, "Online"),
            24: PlayerSessionEntry(24, "Player B", None, False, "Online"),
        },
        game_details=GameDetails(
            seed_hash="AB12",
            word_hash="Chykka Required",
            spoiler=True,
            permalink="<permalink>",
        ),
        state=GameSessionState.IN_PROGRESS,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
    )
    network_client.current_game_session = initial_session

    window = await GameSessionWindow.create_and_update(network_client, game_connection, preset_manager,
                                                       MagicMock(), MagicMock())
    window.update_multiworld_client_status = AsyncMock()

    # Run
    await window.on_game_session_meta_update(second_session)
    window.update_multiworld_client_status.assert_awaited()
    network_client.session_self_update.assert_awaited_once_with(
        game_connection.get_current_inventory.return_value,
        game_connection.current_status,
        game_connection.backend_choice,
    )


@pytest.mark.asyncio
async def test_on_game_session_actions_update(window: GameSessionWindow, default_preset):
    # Setup
    game_session = MagicMock()
    game_session.presets = [default_preset]
    window._game_session = game_session

    # Run
    await window.on_game_session_actions_update(
        GameSessionActions((
            GameSessionAction("A", 0, "B", "Bombs", PickupIndex(0), datetime.datetime(year=2020, month=1, day=5)),
        ))
    )

    texts = [
        window.history_table_widget.item(0, i).text()
        for i in range(5)
    ]
    assert texts == [
        'A',
        'B',
        'Bombs',
        'Temple Grounds/Hive Chamber A/Pickup (Missile)',
        'Sun Jan  5 00:00:00 2020'
    ]


@pytest.mark.parametrize("in_game", [False, True])
@pytest.mark.asyncio
async def test_update_multiworld_client_status(window, in_game):
    # Setup
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
async def test_row_show_preset_summary(window, mocker, preset_manager):
    # Setup
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)

    row = MagicMock()
    window.rows = [row]
    window._game_session = MagicMock()
    window._game_session.presets = [preset_manager.default_preset]

    # Run
    await window._row_show_preset_summary(row)

    # Assert
    execute_dialog.assert_awaited_once()


@pytest.mark.parametrize(["has_background_process", "generation_in_progress", "game_details", "expected_text"], [
    (True, None, None, "Stop"),
    (False, True, None, "Abort generation"),
    (False, None, None, "Generate game"),
    (False, None, True, "Clear generated game"),
])
def test_update_background_process_button(window, has_background_process, generation_in_progress, game_details,
                                          expected_text):
    window._game_session = MagicMock()

    window._background_thread = True if has_background_process else None
    window._game_session.generation_in_progress = generation_in_progress
    window._game_session.game_details = game_details

    # Run
    window.update_background_process_button()

    # Assert
    assert window.background_process_button.text() == expected_text


def test_sync_background_process_to_game_session_other_generation(window):
    window._game_session = MagicMock()
    window._game_session.generation_in_progress = True
    window._generating_game = False

    # Run
    window.sync_background_process_to_game_session()

    # Assert
    assert window.progress_label.text().startswith("Game being generated by")


def test_sync_background_process_to_game_session_stop_background(window):
    window._game_session = MagicMock()
    window._game_session.generation_in_progress = None
    window._background_thread = True
    window._generating_game = True
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_game_session()

    # Assert
    window.stop_background_process.assert_called_once_with()


def test_sync_background_process_to_game_session_nothing(window):
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
async def test_update_logic_settings_window(window, mocker, has_game):
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window._game_session = MagicMock()
    window._logic_settings_window = MagicMock()
    window._game_session.game_details = True if has_game else None

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
async def test_change_password(window, mocker):
    def set_text_value(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue("magoo")
        return QtWidgets.QDialog.Accepted

    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                  side_effect=set_text_value)
    window._admin_global_action = AsyncMock()

    # Run
    await window.change_password()

    # Assert
    execute_dialog.assert_awaited_once()
    window._admin_global_action.assert_awaited_once_with(SessionAdminGlobalAction.CHANGE_PASSWORD, "magoo")


@pytest.mark.asyncio
async def test_generate_game(window, mocker, preset_manager):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.simplified_patcher.generate_layout")
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=5000)

    spoiler = True
    game_session = MagicMock()
    game_session.presets = [preset_manager.default_preset, preset_manager.default_preset]

    window._game_session = game_session
    window._upload_layout_description = AsyncMock()
    window._admin_global_action = AsyncMock()

    # Run
    await window.generate_game(spoiler, retries=3)

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
        options=window._options,
        retries=3,
    )
    window._upload_layout_description.assert_awaited_once_with(mock_generate_layout.return_value)


@pytest.mark.asyncio
async def test_check_dangerous_presets(window, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.No

    game_session = MagicMock()
    game_session.presets = [MagicMock(), MagicMock(), MagicMock()]
    game_session.presets[0].name = "Preset A"
    game_session.presets[0].dangerous_settings.return_value = ["Cake"]
    game_session.presets[1].name = "Preset B"
    game_session.presets[1].dangerous_settings.return_value = ["Bomb", "Knife"]
    game_session.presets[2].dangerous_settings.return_value = []

    window._game_session = game_session
    window.team_players = [MagicMock(), MagicMock()]
    window.team_players[0].player.name = "Crazy Person"
    window.team_players[1].player = None

    permalink = MagicMock()
    permalink.presets = {i: preset for i, preset in enumerate(game_session.presets)}

    # Run
    result = await window._check_dangerous_presets(permalink)

    # Assert
    message = ("The following presets have settings that can cause an impossible game:\n"
               "\nCrazy Person - Preset A: Cake"
               "\nPlayer 2 - Preset B: Bomb, Knife"
               "\n\nDo you want to continue?")
    mock_warning.assert_awaited_once_with(window, "Dangerous preset", message,
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
    assert not result


@pytest.mark.asyncio
async def test_copy_permalink(window, mocker):
    mock_set_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    game_session = MagicMock()
    game_session.game_details.permalink = "<permalink>"

    window._game_session = game_session

    # Run
    await window.copy_permalink()

    # Assert
    execute_dialog.assert_awaited_once()
    assert execute_dialog.call_args.args[0].textValue() == "<permalink>"
    mock_set_clipboard.assert_called_once_with("<permalink>")


@pytest.mark.asyncio
async def test_import_permalink(window, mocker):
    mock_permalink_dialog = mocker.patch("randovania.gui.game_session_window.PermalinkDialog")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    execute_dialog.return_value = QtWidgets.QDialog.Accepted
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.Yes

    permalink = mock_permalink_dialog.return_value.get_permalink_from_field.return_value
    permalink.player_count = 2
    permalink.presets = {0: MagicMock(), 1: MagicMock()}
    permalink.presets[0].is_same_configuration.return_value = False

    game_session = MagicMock()
    game_session.num_rows = 2
    game_session.presets = [MagicMock(), MagicMock()]

    window._game_session = game_session
    window.generate_game_with_permalink = AsyncMock()

    # Run
    await window.import_permalink()

    # Assert
    execute_dialog.assert_awaited_once_with(mock_permalink_dialog.return_value)
    mock_warning.assert_awaited_once_with(window, "Different presets", ANY, ANY, QtWidgets.QMessageBox.No)
    window.generate_game_with_permalink.assert_awaited_once_with(permalink, retries=None)


@pytest.mark.parametrize(["expecting_kick", "already_kicked"], [
    (False, True),
    (False, False),
    (True, False),
])
@pytest.mark.asyncio
async def test_on_kicked(skip_qtbot, window, mocker, expecting_kick, already_kicked):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window.network_client.leave_game_session = AsyncMock()
    window._game_session = MagicMock()
    window._already_kicked = already_kicked
    window._expecting_kick = expecting_kick
    window.close = MagicMock(return_value=None)

    # Run
    await window._on_kicked()
    if not already_kicked:
        skip_qtbot.waitUntil(window.close)

    # Assert
    if already_kicked:
        window.network_client.leave_game_session.assert_not_awaited()
        mock_warning.assert_not_awaited()
        window.close.assert_not_called()
    else:
        window.network_client.leave_game_session.assert_awaited_once_with(False)
        if expecting_kick:
            mock_warning.assert_not_awaited()
        else:
            mock_warning.assert_awaited_once()
        window.close.assert_called_once_with()


@pytest.mark.parametrize("exception", [False, True])
@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.asyncio
async def test_delete_session(window, mocker, accept, exception, monkeypatch):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.Yes if accept else QtWidgets.QMessageBox.No

    window.network_client.session_admin_global = AsyncMock()
    if exception and accept:
        def re_raise_exception(_, v, __):
            raise v

        monkeypatch.setattr(sys, "excepthook", re_raise_exception)

        window.network_client.session_admin_global.side_effect = RuntimeError("error")
        expectation = pytest.raises(RuntimeError, match="error")
    else:
        expectation = contextlib.nullcontext()

    # Run
    with expectation:
        await window.delete_session()

    # Assert
    mock_warning.assert_awaited_once()
    if accept:
        window.network_client.session_admin_global.assert_awaited_once_with(SessionAdminGlobalAction.DELETE_SESSION,
                                                                            None)
        assert window._expecting_kick != exception
    else:
        window.network_client.session_admin_global.assert_not_awaited()
        assert not window._expecting_kick


@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.asyncio
async def test_finish_session(window, accept, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.Yes if accept else QtWidgets.QMessageBox.No

    window.network_client.session_admin_global = AsyncMock()

    # Run
    await window.finish_session()

    # Assert
    mock_warning.assert_awaited_once()
    if accept:
        window.network_client.session_admin_global.assert_awaited_once_with(SessionAdminGlobalAction.FINISH_SESSION,
                                                                            None)
    else:
        window.network_client.session_admin_global.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_iso(window, mocker, preset_manager, echoes_game_description):
    mock_input_dialog = mocker.patch("randovania.gui.game_session_window.GameInputDialog")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    window._game_session = MagicMock()
    window._game_session.players[window.network_client.current_user.id].is_observer = False
    window._game_session.players[window.network_client.current_user.id].row = 0
    window._game_session.presets = {0: preset_manager.default_preset}
    layout_configuration = preset_manager.default_preset.get_preset().configuration
    window.network_client.session_admin_player = AsyncMock()

    patcher_provider = typing.cast(MagicMock, window._window_manager.patcher_provider)
    patcher = patcher_provider.patcher_for_game.return_value
    patcher.is_busy = False

    # Run
    await window.save_iso()

    # Assert
    patcher_provider.patcher_for_game.assert_called_once_with(layout_configuration.game)
    mock_execute_dialog.assert_awaited_once_with(mock_input_dialog.return_value)
    patcher.patch_game.assert_called_once_with(
        mock_input_dialog.return_value.input_file,
        mock_input_dialog.return_value.output_file,
        window.network_client.session_admin_player.return_value,
        window._options.internal_copies_path,
        progress_update=ANY,
    )


@pytest.mark.parametrize("dialog_response", [QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel])
@pytest.mark.parametrize("is_member", [False, True])
@pytest.mark.asyncio
async def test_on_close_event(window: GameSessionWindow, mocker, dialog_response, is_member):
    # Setup
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock,
                                  return_value=dialog_response)
    super_close_event = mocker.patch("PySide2.QtWidgets.QMainWindow.closeEvent")
    event = MagicMock()
    window._game_session = MagicMock()
    window._game_session.players = [window.network_client.current_user.id] if is_member else []
    window.network_client.leave_game_session = AsyncMock()
    window.network_client.connection_state.is_disconnected = dialog_response == QMessageBox.Yes

    # Run
    await window._on_close_event(event)

    if is_member:
        execute_dialog.assert_awaited_once()
    else:
        execute_dialog.assert_not_awaited()

    if is_member and dialog_response == QMessageBox.Cancel:
        event.ignore.assert_called_once_with()
        super_close_event.assert_not_called()
    else:
        event.ignore.assert_not_called()
        super_close_event.assert_called_once_with(event)

    if is_member and dialog_response != QMessageBox.Cancel:
        window.network_client.leave_game_session.assert_awaited_once_with(dialog_response == QMessageBox.Yes)
    else:
        window.network_client.leave_game_session.assert_not_awaited()
