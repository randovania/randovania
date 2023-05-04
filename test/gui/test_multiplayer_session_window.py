import datetime
import json
import uuid
from unittest.mock import MagicMock, AsyncMock, ANY

import pytest
from PySide6 import QtWidgets

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.gui.multiplayer_session_window import MultiplayerSessionWindow
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.error import NotAuthorizedForAction
from randovania.network_common.multiplayer_session import (
    MultiplayerSessionEntry, MultiplayerUser, User, MultiplayerWorldAction,
    MultiplayerWorldActions, GameDetails, MultiplayerWorld,
)
from randovania.network_common.session_state import MultiplayerSessionState


@pytest.fixture()
async def window(skip_qtbot) -> MultiplayerSessionWindow:
    window = MultiplayerSessionWindow(MagicMock(), MagicMock(), MagicMock())
    skip_qtbot.addWidget(window)
    window.connect_to_events()
    return window


@pytest.fixture()
def sample_session(preset_manager):
    u1 = uuid.UUID('53308c10-c283-4be5-b5d2-1761c81a871b')
    u2 = uuid.UUID('4bdb294e-9059-4fdf-9822-3f649023249a')

    return MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1", id=u1, preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
            MultiplayerWorld(
                name="W2", id=u2, preset_raw=json.dumps(
                    preset_manager.default_preset.as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(12, "Player A", True, worlds={u1: "Online"}),
        ],
        game_details=None,
        state=MultiplayerSessionState.SETUP,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
    )


async def test_on_session_meta_update(preset_manager, skip_qtbot, sample_session):
    # Setup
    network_client = MagicMock()
    network_client.current_user = User(id=12, name="Player A")
    network_client.server_call = AsyncMock()
    game_connection = MagicMock(spec=GameConnection)
    game_connection.executor = AsyncMock()
    game_connection.pretty_current_status = "Maybe Connected"
    game_connection.lock_identifier = None

    u1 = uuid.UUID('53308c10-c283-4be5-b5d2-1761c81a871b')
    u2 = uuid.UUID('4bdb294e-9059-4fdf-9822-3f649023249a')

    initial_session = sample_session
    second_session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1", id=u1, preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(12, "Player A", True, worlds={u1: "Online"}),
            MultiplayerUser(24, "Player B", False, {}),
        ],
        game_details=GameDetails(
            seed_hash="AB12",
            word_hash="Chykka Required",
            spoiler=True,
        ),
        state=MultiplayerSessionState.IN_PROGRESS,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
    )
    window = await MultiplayerSessionWindow.create_and_update(network_client, initial_session,
                                                              MagicMock(), MagicMock())
    skip_qtbot.addWidget(window)

    # Run
    await window.on_meta_update(second_session)
    network_client.server_call.assert_awaited_once_with(
        'multiplayer_request_session_update', 1234
    )


async def test_on_session_actions_update(window: MultiplayerSessionWindow, sample_session):
    # Setup
    window._session = sample_session
    timestamp = datetime.datetime(year=2020, month=1, day=5)

    # Run
    await window.on_actions_update(
        MultiplayerWorldActions(
            session_id=sample_session.id,
            actions=[
                MultiplayerWorldAction(
                    provider=sample_session.worlds[0].id,
                    receiver=sample_session.worlds[1].id,
                    pickup="Bombs",
                    location=0,
                    time=timestamp
                ),
            ],
        )
    )

    texts = [
        window.tab_history.item(0, i).text()
        for i in range(5)
    ]
    assert texts == [
        'W1',
        'W2',
        'Bombs',
        'Temple Grounds/Hive Chamber A/Pickup (Missile)',
        timestamp.strftime("%c")
    ]


@pytest.mark.parametrize(["has_background_process", "generation_in_progress", "game_details", "expected_text"], [
    (True, None, None, "Stop"),
    (False, True, None, "Abort generation"),
    (False, None, None, "Generate game"),
    (False, None, True, "Clear generated game"),
])
def test_update_background_process_button(window: MultiplayerSessionWindow, has_background_process,
                                          generation_in_progress, game_details, expected_text):
    window._session = MagicMock()

    window._background_thread = True if has_background_process else None
    window._session.generation_in_progress = generation_in_progress
    window._session.game_details = game_details

    # Run
    window.update_background_process_button()

    # Assert
    assert window.background_process_button.text() == expected_text


def test_sync_background_process_to_session_other_generation(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    window._session.generation_in_progress = True
    window._generating_game = False

    # Run
    window.sync_background_process_to_session()

    # Assert
    assert window.progress_label.text().startswith("Game being generated by")


def test_sync_background_process_to_session_stop_background(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    window._session.generation_in_progress = None
    window._background_thread = True
    window._generating_game = True
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_session()

    # Assert
    window.stop_background_process.assert_called_once_with()


def test_sync_background_process_to_session_nothing(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    window._session.generation_in_progress = None
    window._background_thread = None
    window._generating_game = False
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_session()

    # Assert
    assert window.progress_label.text() == ""


@pytest.mark.parametrize("has_game", [False, True])
async def test_update_logic_settings_window(window: MultiplayerSessionWindow, mocker, has_game):
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window._session = MagicMock()
    window._logic_settings_window = MagicMock()
    window._session.game_details = True if has_game else None

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
        return QtWidgets.QDialog.DialogCode.Accepted

    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                  side_effect=set_text_value)
    window._admin_global_action = AsyncMock()

    # Run
    await getattr(window, method_name)()

    # Assert
    execute_dialog.assert_awaited_once()
    window._admin_global_action.assert_awaited_once_with(action, "magoo")


async def test_generate_game(window: MultiplayerSessionWindow, mocker, preset_manager):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.simplified_patcher.generate_layout")
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=5000)
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    spoiler = True
    session = MagicMock()
    session.worlds = [
        MultiplayerWorld(id=uuid.uuid4(), name="W1", preset_raw=json.dumps(preset_manager.default_preset.as_json)),
        MultiplayerWorld(id=uuid.uuid4(), name="W2", preset_raw=json.dumps(preset_manager.default_preset.as_json)),
    ]

    window._session = session
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


async def test_check_dangerous_presets(window: MultiplayerSessionWindow, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.StandardButton.No

    presets = [MagicMock(), MagicMock(), MagicMock()]
    presets[0].dangerous_settings.return_value = ["Cake"]
    presets[1].dangerous_settings.return_value = ["Bomb", "Knife"]
    presets[2].dangerous_settings.return_value = []

    session = MagicMock()
    session.worlds = [MagicMock(), MagicMock(), MagicMock()]
    session.worlds[0].name = "Crazy Person"
    session.worlds[1].name = "World 2"
    session.worlds[2].name = "World 3"

    window._session = session

    permalink = MagicMock(spec=Permalink)
    permalink.parameters = MagicMock(spec=GeneratorParameters)
    permalink.parameters.presets = presets

    # Run
    result = await window._check_dangerous_presets(permalink)

    # Assert
    message = ("The following presets have settings that can cause an impossible game:\n"
               "\nCrazy Person: Cake"
               "\nWorld 2: Bomb, Knife"
               "\n\nDo you want to continue?")
    mock_warning.assert_awaited_once_with(
        window, "Dangerous preset", message,
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
    assert not result


async def test_copy_permalink_is_admin(window: MultiplayerSessionWindow, mocker):
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


async def test_copy_permalink_not_admin(window: MultiplayerSessionWindow, mocker):
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


async def test_import_permalink(window: MultiplayerSessionWindow, mocker):
    mock_permalink_dialog = mocker.patch("randovania.gui.multiplayer_session_window.PermalinkDialog")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    execute_dialog.return_value = QtWidgets.QDialog.DialogCode.Accepted
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.StandardButton.Yes

    permalink = mock_permalink_dialog.return_value.get_permalink_from_field.return_value
    permalink.parameters.player_count = 2
    permalink.parameters.presets = [MagicMock(), MagicMock()]
    permalink.parameters.presets[0].is_same_configuration.return_value = False

    session = MagicMock()
    session.num_rows = 2
    session.worlds = [MagicMock(), MagicMock()]

    window._session = session
    window.generate_game_with_permalink = AsyncMock()

    # Run
    await window.import_permalink()

    # Assert
    execute_dialog.assert_awaited_once_with(mock_permalink_dialog.return_value)
    mock_warning.assert_awaited_once_with(window, "Different presets", ANY, ANY,
                                          QtWidgets.QMessageBox.StandardButton.No)
    window.generate_game_with_permalink.assert_awaited_once_with(permalink, retries=None)


@pytest.mark.parametrize("already_kicked", [True, False])
async def test_on_kicked(skip_qtbot, window: MultiplayerSessionWindow, mocker, already_kicked):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window.network_client.leave_multiplayer_session = AsyncMock()
    window._session = MagicMock()
    window._already_kicked = already_kicked
    window.close = MagicMock(return_value=None)

    # Run
    await window._on_kicked()
    if not already_kicked:
        skip_qtbot.waitUntil(window.close)

    # Assert
    if already_kicked:
        window.network_client.leave_multiplayer_session.assert_not_awaited()
        mock_warning.assert_not_awaited()
        window.close.assert_not_called()
    else:
        window.network_client.leave_multiplayer_session.assert_awaited_once_with(window._session)
        mock_warning.assert_awaited_once()
        window.close.assert_called_once_with()


@pytest.mark.parametrize("accept", [False, True])
async def test_finish_session(window: MultiplayerSessionWindow, accept, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = (
        QtWidgets.QMessageBox.StandardButton.Yes if accept else QtWidgets.QMessageBox.StandardButton.No
    )

    window._session = MagicMock()
    window.network_client.session_admin_global = AsyncMock()

    # Run
    await window.finish_session()

    # Assert
    mock_warning.assert_awaited_once()
    if accept:
        window.network_client.session_admin_global.assert_awaited_once_with(
            window._session, SessionAdminGlobalAction.FINISH_SESSION, None)
    else:
        window.network_client.session_admin_global.assert_not_awaited()


async def test_game_export_listener(window: MultiplayerSessionWindow, mocker, echoes_game_description,
                                    preset_manager):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QtWidgets.QDialog.DialogCode.Accepted)

    game = MagicMock()
    window._session = MagicMock()
    window._session.worlds = [MultiplayerWorld(
        id=uuid.uuid4(),
        name="W1",
        preset_raw=json.dumps(preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json)
    )]
    window.network_client.session_admin_player = AsyncMock()

    patch_data = MagicMock()
    game.exporter.is_busy = False

    # Run
    await window.game_export_listener(game, patch_data)

    # Assert
    game.gui.export_dialog.assert_called_once_with(
        window._options,
        patch_data,
        window._session.game_details.word_hash,
        False,
        [RandovaniaGame.METROID_PRIME_ECHOES],
    )
    mock_execute_dialog.assert_awaited_once_with(game.gui.export_dialog.return_value)
    game.exporter.export_game.assert_called_once_with(
        patch_data,
        game.gui.export_dialog.return_value.get_game_export_params.return_value,
        progress_update=ANY,
    )


@pytest.mark.parametrize("is_member", [False, True])
async def test_on_close_event(window: MultiplayerSessionWindow, mocker, is_member):
    # Setup
    super_close_event = mocker.patch("PySide6.QtWidgets.QMainWindow.closeEvent")
    event = MagicMock()
    window._session = MagicMock()
    window._session.users = [window.network_client.current_user.id] if is_member else []
    window.network_client.leave_multiplayer_session = AsyncMock()
    window.network_client.connection_state.is_disconnected = False

    # Run
    await window._on_close_event(event)
    event.ignore.assert_not_called()
    super_close_event.assert_called_once_with(event)

    if is_member:
        window.network_client.leave_multiplayer_session.assert_awaited_once_with(window._session)
    else:
        window.network_client.leave_multiplayer_session.assert_not_awaited()
