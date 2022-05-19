import datetime

import pytest
from PySide6 import QtWidgets
from mock import MagicMock, AsyncMock, ANY

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.gui.game_session_window import GameSessionWindow
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.network_client.game_session import (
    GameSessionEntry, PlayerSessionEntry, User, GameSessionAction,
    GameSessionActions, GameDetails,
)
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.error import NotAuthorizedForAction
from randovania.network_common.session_state import GameSessionState


@pytest.fixture(name="window")
async def _window(skip_qtbot):
    game_connection = MagicMock(spec=GameConnection)
    game_connection.executor = AsyncMock()
    game_connection.lock_identifier = None
    game_connection.pretty_current_status = "Pretty Status"
    window = GameSessionWindow(MagicMock(), game_connection, MagicMock(), MagicMock(), MagicMock())
    skip_qtbot.addWidget(window)
    window.connect_to_events()
    return window


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
        presets=[preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES),
                 preset_manager.default_preset],
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
        presets=[preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES)],
        players={
            12: PlayerSessionEntry(12, "Player A", 0, True, "Online"),
            24: PlayerSessionEntry(24, "Player B", None, False, "Online"),
        },
        game_details=GameDetails(
            seed_hash="AB12",
            word_hash="Chykka Required",
            spoiler=True,
        ),
        state=GameSessionState.IN_PROGRESS,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
    )
    network_client.current_game_session = initial_session

    window = await GameSessionWindow.create_and_update(network_client, game_connection, preset_manager,
                                                       MagicMock(), MagicMock())
    window.update_multiworld_client_status = AsyncMock()
    skip_qtbot.addWidget(window)

    # Run
    await window.on_game_session_meta_update(second_session)
    window.update_multiworld_client_status.assert_awaited()
    network_client.session_self_update.assert_awaited_once_with(
        game_connection.get_current_inventory.return_value,
        game_connection.current_status,
        game_connection.backend_choice,
    )


async def test_on_game_session_actions_update(window: GameSessionWindow, default_echoes_preset):
    # Setup
    game_session = MagicMock()
    game_session.presets = [default_echoes_preset]
    window._game_session = game_session
    timestamp = datetime.datetime(year=2020, month=1, day=5)

    # Run
    await window.on_game_session_actions_update(
        GameSessionActions((
            GameSessionAction("A", 0, "B", "Bombs", PickupIndex(0), timestamp),
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
        timestamp.strftime("%c")
    ]


@pytest.mark.parametrize("in_game", [False, True])
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


@pytest.mark.parametrize(["action", "method_name"], [
    (SessionAdminGlobalAction.CHANGE_TITLE, "rename_session"),
    (SessionAdminGlobalAction.CHANGE_PASSWORD, "change_password"),
    (SessionAdminGlobalAction.DUPLICATE_SESSION, "duplicate_session"),
])
async def test_change_password_title_or_duplicate(window, mocker, action, method_name):
    def set_text_value(dialog: QtWidgets.QInputDialog):
        dialog.setTextValue("magoo")
        return QtWidgets.QDialog.Accepted

    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                  side_effect=set_text_value)
    window._admin_global_action = AsyncMock()

    # Run
    await getattr(window, method_name)()

    # Assert
    execute_dialog.assert_awaited_once()
    window._admin_global_action.assert_awaited_once_with(action, "magoo")


async def test_generate_game(window, mocker, preset_manager):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.simplified_patcher.generate_layout")
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=5000)
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    spoiler = True
    game_session = MagicMock()
    game_session.presets = [preset_manager.default_preset, preset_manager.default_preset]

    window._game_session = game_session
    window._upload_layout_description = AsyncMock()
    window._admin_global_action = AsyncMock()

    # Run
    await window.generate_game(spoiler, retries=3)

    # Assert
    mock_warning.assert_awaited_once_with(
        window, "Multiworld Limitation", ANY,
    )
    mock_randint.assert_called_once_with(0, 2 ** 31)
    mock_generate_layout.assert_called_once_with(
        progress_update=ANY,
        parameters=GeneratorParameters(
            seed_number=mock_randint.return_value,
            spoiler=spoiler,
            presets=[
                preset_manager.default_preset.get_preset(),
                preset_manager.default_preset.get_preset(),
            ],
        ),
        options=window._options,
        retries=3,
    )
    window._upload_layout_description.assert_awaited_once_with(mock_generate_layout.return_value)


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

    permalink = MagicMock(spec=Permalink)
    permalink.parameters = MagicMock(spec=GeneratorParameters)
    permalink.parameters.presets = list(game_session.presets)

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


async def test_copy_permalink_is_admin(window, mocker):
    mock_set_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window._admin_global_action = AsyncMock(return_value="<permalink>")

    # Run
    await window.copy_permalink()

    # Assert
    window._admin_global_action.assert_awaited_once_with(SessionAdminGlobalAction.REQUEST_PERMALINK, None)
    execute_dialog.assert_awaited_once()
    assert execute_dialog.call_args.args[0].textValue() == "<permalink>"
    mock_set_clipboard.assert_called_once_with("<permalink>")


async def test_copy_permalink_not_admin(window, mocker):
    mock_set_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    execute_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    execute_dialog: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window._admin_global_action = AsyncMock(side_effect=NotAuthorizedForAction)

    # Run
    await window.copy_permalink()

    # Assert
    window._admin_global_action.assert_awaited_once_with(SessionAdminGlobalAction.REQUEST_PERMALINK, None)
    execute_warning.assert_awaited_once_with(window, "Unauthorized", "You're not authorized to perform that action.")
    execute_dialog.assert_not_awaited()
    mock_set_clipboard.assert_not_called()


async def test_import_permalink(window, mocker):
    mock_permalink_dialog = mocker.patch("randovania.gui.game_session_window.PermalinkDialog")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    execute_dialog.return_value = QtWidgets.QDialog.Accepted
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.Yes

    permalink = mock_permalink_dialog.return_value.get_permalink_from_field.return_value
    permalink.parameters.player_count = 2
    permalink.parameters.presets = [MagicMock(), MagicMock()]
    permalink.parameters.presets[0].is_same_configuration.return_value = False

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


@pytest.mark.parametrize("already_kicked", [True, False])
async def test_on_kicked(skip_qtbot, window, mocker, already_kicked):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window.network_client.leave_game_session = AsyncMock()
    window._game_session = MagicMock()
    window._already_kicked = already_kicked
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
        mock_warning.assert_awaited_once()
        window.close.assert_called_once_with()


@pytest.mark.parametrize("accept", [False, True])
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


async def test_save_iso(window, mocker, echoes_game_description):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.Accepted)

    preset = MagicMock()
    # preset.game = RandovaniaGame.METROID_PRIME_ECHOES
    window._game_session = MagicMock()
    window._game_session.players[window.network_client.current_user.id].is_observer = False
    window._game_session.players[window.network_client.current_user.id].row = 0
    window._game_session.presets = [preset]
    window.network_client.session_admin_player = AsyncMock()

    patch_data = window.network_client.session_admin_player.return_value

    game = preset.game
    game.exporter.is_busy = False

    # Run
    await window.save_iso()

    # Assert
    game.gui.export_dialog.assert_called_once_with(
        window._options,
        patch_data,
        window._game_session.game_details.word_hash,
        False,
        [game],
    )
    mock_execute_dialog.assert_awaited_once_with(game.gui.export_dialog.return_value)
    game.exporter.export_game.assert_called_once_with(
        patch_data,
        game.gui.export_dialog.return_value.get_game_export_params.return_value,
        progress_update=ANY,
    )


@pytest.mark.parametrize("is_member", [False, True])
async def test_on_close_event(window: GameSessionWindow, mocker, is_member):
    # Setup
    super_close_event = mocker.patch("PySide6.QtWidgets.QMainWindow.closeEvent")
    event = MagicMock()
    window._game_session = MagicMock()
    window._game_session.players = [window.network_client.current_user.id] if is_member else []
    window.network_client.leave_game_session = AsyncMock()
    window.network_client.connection_state.is_disconnected = False

    # Run
    await window._on_close_event(event)
    event.ignore.assert_not_called()
    super_close_event.assert_called_once_with(event)

    if is_member:
        window.network_client.leave_game_session.assert_awaited_once_with(False)
    else:
        window.network_client.leave_game_session.assert_not_awaited()
