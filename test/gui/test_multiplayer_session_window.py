from __future__ import annotations

import asyncio
import contextlib
import datetime
import json
import uuid
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock, call

import pytest
from PySide6 import QtCore, QtWidgets

from randovania.game_connection.game_connection import GameConnection
from randovania.games.game import RandovaniaGame
from randovania.gui.lib import model_lib
from randovania.gui.lib.window_manager import WindowManager
from randovania.gui.multiplayer_session_window import MultiplayerSessionWindow
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.layout.versioned_preset import VersionedPreset
from randovania.lib import string_lib
from randovania.lib.container_lib import zip2
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import (
    GameDetails,
    MultiplayerSessionAction,
    MultiplayerSessionActions,
    MultiplayerSessionAuditEntry,
    MultiplayerSessionAuditLog,
    MultiplayerSessionEntry,
    MultiplayerUser,
    MultiplayerWorld,
    User,
    UserWorldDetail,
)
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock
    from pytest_mock import MockerFixture

    from randovania.gui.dialog.text_prompt_dialog import TextPromptDialog


@pytest.fixture()
async def window(skip_qtbot) -> MultiplayerSessionWindow:
    window = MultiplayerSessionWindow(MagicMock(), MagicMock(spec=WindowManager), MagicMock())
    skip_qtbot.addWidget(window)
    window.connect_to_events()
    return window


@pytest.fixture()
def sample_session(preset_manager):
    u1 = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    u2 = uuid.UUID("4bdb294e-9059-4fdf-9822-3f649023249a")
    u3 = uuid.UUID("47a8aec3-3149-4c76-b5c1-f86a9d3a5190")

    return MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1",
                id=u1,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
            MultiplayerWorld(
                name="W2",
                id=u2,
                preset_raw=json.dumps(preset_manager.default_preset.as_json),
            ),
            MultiplayerWorld(
                name="W3",
                id=u3,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={
                    u1: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    )
                },
            ),
        ],
        game_details=None,
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
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

    u1 = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")

    initial_session = sample_session
    second_session = MultiplayerSessionEntry(
        id=1234,
        name="The Session",
        worlds=[
            MultiplayerWorld(
                name="W1",
                id=u1,
                preset_raw=json.dumps(
                    preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json
                ),
            ),
        ],
        users_list=[
            MultiplayerUser(
                12,
                "Player A",
                True,
                True,
                worlds={
                    u1: UserWorldDetail(
                        GameConnectionStatus.InGame, datetime.datetime(2019, 1, 3, 2, 50, tzinfo=datetime.UTC)
                    )
                },
            ),
            MultiplayerUser(24, "Player B", False, False, {}),
        ],
        game_details=GameDetails(
            seed_hash="AB12",
            word_hash="Chykka Required",
            spoiler=True,
        ),
        visibility=MultiplayerSessionVisibility.VISIBLE,
        generation_in_progress=None,
        allowed_games=[RandovaniaGame.METROID_PRIME_ECHOES],
        allow_coop=False,
        allow_everyone_claim_world=True,
    )
    window = await MultiplayerSessionWindow.create_and_update(
        network_client, initial_session.id, MagicMock(spec=WindowManager), MagicMock()
    )
    skip_qtbot.addWidget(window)

    # Run
    await window.on_meta_update(second_session)
    network_client.server_call.assert_awaited_once_with("multiplayer_request_session_update", 1234)


async def test_on_session_actions_update(window: MultiplayerSessionWindow, sample_session):
    # Setup
    window._session = sample_session
    timestamp = datetime.datetime(year=2020, month=1, day=5)

    # Run
    await window.on_actions_update(
        MultiplayerSessionActions(
            session_id=sample_session.id,
            actions=[
                MultiplayerSessionAction(
                    provider=sample_session.worlds[0].id,
                    receiver=sample_session.worlds[1].id,
                    pickup="Bombs",
                    location=0,
                    time=timestamp,
                ),
                MultiplayerSessionAction(
                    provider=sample_session.worlds[0].id,
                    receiver=sample_session.worlds[2].id,
                    pickup="Bombs",
                    location=1,
                    time=timestamp,
                ),
                MultiplayerSessionAction(
                    provider=sample_session.worlds[2].id,
                    receiver=sample_session.worlds[1].id,
                    pickup="Missile",
                    location=2,
                    time=timestamp,
                ),
                MultiplayerSessionAction(
                    provider=sample_session.worlds[1].id,
                    receiver=sample_session.worlds[0].id,
                    pickup="Missile",
                    location=2,
                    time=timestamp,
                ),
            ],
        )
    )

    dt = QtCore.QDateTime(2020, 1, 5, 0, 0, 0, 0, 0)

    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W2", "Bombs", "Temple Grounds/Hive Chamber A/Pickup (Missile)", dt],
        ["W1", "W3", "Bombs", "Temple Grounds/Hall of Honored Dead/Pickup (Seeker Launcher)", dt],
        ["W3", "W2", "Missile", "Temple Grounds/Hive Chamber B/Pickup (Missile)", dt],
        ["W2", "W1", "Missile", "Intro/Explosive Depot/Pickup (Explosive)", dt],
    ]

    window.history_filter_edit.setText("Missile")
    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W2", "Bombs", "Temple Grounds/Hive Chamber A/Pickup (Missile)", dt],
        ["W3", "W2", "Missile", "Temple Grounds/Hive Chamber B/Pickup (Missile)", dt],
        ["W2", "W1", "Missile", "Intro/Explosive Depot/Pickup (Explosive)", dt],
    ]

    window.history_filter_edit.setText("Hive Chamber")
    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W2", "Bombs", "Temple Grounds/Hive Chamber A/Pickup (Missile)", dt],
        ["W3", "W2", "Missile", "Temple Grounds/Hive Chamber B/Pickup (Missile)", dt],
    ]

    window.history_item_proxy.set_provider_filter("W1")
    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W2", "Bombs", "Temple Grounds/Hive Chamber A/Pickup (Missile)", dt],
    ]

    window.history_filter_edit.setText("")
    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W2", "Bombs", "Temple Grounds/Hive Chamber A/Pickup (Missile)", dt],
        ["W1", "W3", "Bombs", "Temple Grounds/Hall of Honored Dead/Pickup (Seeker Launcher)", dt],
    ]

    window.history_item_proxy.set_receiver_filter("W3")
    assert model_lib.get_texts(window.history_item_proxy) == [
        ["W1", "W3", "Bombs", "Temple Grounds/Hall of Honored Dead/Pickup (Seeker Launcher)", dt],
    ]

    window.history_filter_edit.setText("Missile")
    assert model_lib.get_texts(window.history_item_proxy) == []


@pytest.mark.parametrize(
    ("generation_in_progress", "game_details", "expected_text"),
    [
        (True, None, "Abort generation"),
        (None, None, "Generate game"),
        (None, True, "Clear generated game"),
    ],
)
async def test_update_generate_game_button(
    window: MultiplayerSessionWindow, generation_in_progress, game_details, expected_text
):
    window._session = MagicMock()
    window._session.generation_in_progress = generation_in_progress
    window._session.game_details = game_details

    # Run
    window.update_generate_game_button()

    # Assert
    assert window.generate_game_button.text() == expected_text


async def test_sync_background_process_to_session_other_generation(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    window._session.generation_in_progress = True
    window._generating_game = False

    # Run
    window.sync_background_process_to_session()

    # Assert
    assert window.progress_label.text().startswith("Game being generated by")


async def test_sync_background_process_to_session_stop_background(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    window._session.generation_in_progress = None
    window._background_thread = True
    window._generating_game = True
    window.stop_background_process = MagicMock()

    # Run
    window.sync_background_process_to_session()

    # Assert
    window.stop_background_process.assert_called_once_with()


async def test_sync_background_process_to_session_nothing(window: MultiplayerSessionWindow):
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


@pytest.mark.parametrize("accept", [QtWidgets.QDialog.DialogCode.Accepted, QtWidgets.QDialog.DialogCode.Rejected])
@pytest.mark.parametrize(
    "method_name",
    [
        "rename_session",
        "change_password",
        "duplicate_session",
    ],
)
async def test_change_password_title_or_duplicate(window: MultiplayerSessionWindow, mocker, method_name, accept):
    def set_text_value(dialog: TextPromptDialog):
        dialog.prompt_edit.setText("magoo")
        return accept

    api_method = AsyncMock()
    setattr(window.game_session_api, method_name, api_method)

    execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock, side_effect=set_text_value
    )
    window._session = MagicMock()
    window._session.name = "OldName"

    # Run
    await getattr(window, method_name)()

    # Assert
    execute_dialog.assert_awaited_once()
    if accept == QtWidgets.QDialog.DialogCode.Accepted:
        api_method.assert_awaited_once_with("magoo")
    else:
        api_method.assert_not_awaited()


@pytest.mark.parametrize("accept", [False, True])
def test_export_all_presets(
    window: MultiplayerSessionWindow, mocker: MockerFixture, sample_session: MultiplayerSessionEntry, accept, tmp_path
):
    # Setup
    window._session = sample_session
    fake_export_path = tmp_path.joinpath("exported_presets")
    fake_export_path.mkdir(parents=True, exist_ok=True)

    prompt_user_for_preset_folder = mocker.patch(
        "randovania.gui.lib.common_qt_lib.prompt_user_for_preset_folder",
        return_value=fake_export_path if accept else None,
    )

    world_names = [world.name.replace("-", "_") for world in sample_session.worlds]
    games = [world.preset.game.short_name for world in sample_session.worlds]
    owner_names = [sample_session.users_list[0].name.replace("-", "_"), "Unclaimed", "Unclaimed"]
    extension = VersionedPreset.file_extension()
    export_filenames = [
        string_lib.sanitize_for_path(f"World{i + 1}-{game}-{owner_name}-{world_name}") + f".{extension}"
        for i, game, owner_name, world_name in zip(range(len(world_names)), games, owner_names, world_names)
    ]

    # Run
    window.export_all_presets()

    # Assert
    prompt_user_for_preset_folder.assert_called()

    if accept:
        for filename in export_filenames:
            assert fake_export_path.joinpath(filename).is_file()
    else:
        assert len(list(fake_export_path.iterdir())) == 0


@pytest.fixture()
def prepare_to_upload_layout():
    result = MagicMock(spec=contextlib.AbstractAsyncContextManager)
    result.__aenter__ = AsyncMock()
    result.__aexit__ = AsyncMock()
    return result


@pytest.mark.parametrize("is_ready", [False, True])
async def test_generate_game(
    window: MultiplayerSessionWindow, mocker, preset_manager, prepare_to_upload_layout, is_ready
):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.generator_frontend.generate_layout")
    mock_randint: MagicMock = mocker.patch("random.randint", return_value=5000)
    mock_yes_no_prompt: AsyncMock = mocker.patch(
        "randovania.gui.lib.async_dialog.yes_no_prompt", new_callable=AsyncMock, return_value=True
    )
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    spoiler = True
    session = MagicMock()
    session.users = {1: MultiplayerUser(1, "You", False, is_ready, {})}
    session.worlds = [
        MultiplayerWorld(id=uuid.uuid4(), name="W1", preset_raw=json.dumps(preset_manager.default_preset.as_json)),
        MultiplayerWorld(id=uuid.uuid4(), name="W2", preset_raw=json.dumps(preset_manager.default_preset.as_json)),
    ]

    window._session = session
    layout = mock_generate_layout.return_value

    uploader = prepare_to_upload_layout.__aenter__.return_value
    window.game_session_api.prepare_to_upload_layout = MagicMock(return_value=prepare_to_upload_layout)

    # Run
    await window.generate_game(spoiler, retries=3)

    # Assert
    if is_ready:
        mock_yes_no_prompt.assert_not_awaited()
    else:
        mock_yes_no_prompt.assert_awaited_once_with(
            window,
            "User not Ready",
            "The following users are not ready. Do you want to continue generating a game?\n\nYou",
        )

    mock_warning.assert_awaited_once_with(
        window,
        "Multiworld Limitation",
        ANY,
    )
    mock_randint.assert_called_once_with(0, 2**31)
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
        world_names=["W1", "W2"],
    )
    window.game_session_api.prepare_to_upload_layout.assert_called_once_with(
        [session.worlds[0].id, session.worlds[1].id]
    )
    uploader.assert_awaited_once_with(layout)
    layout.save_to_file.assert_called_once_with(
        window._options.data_dir.joinpath(f"last_multiplayer_{session.id}.rdvgame")
    )


async def test_generate_game_no_ready_abort(window: MultiplayerSessionWindow, mocker, preset_manager):
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.generator_frontend.generate_layout")
    mock_yes_no_prompt: AsyncMock = mocker.patch(
        "randovania.gui.lib.async_dialog.yes_no_prompt", new_callable=AsyncMock, return_value=False
    )
    mock_warning: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    spoiler = True
    session = MagicMock()
    session.users = {1: MultiplayerUser(1, "You", False, False, {})}
    window._session = session

    window.game_session_api.prepare_to_upload_layout = MagicMock()

    # Run
    await window.generate_game(spoiler, retries=3)

    # Assert
    mock_yes_no_prompt.assert_awaited_once_with(
        window, "User not Ready", "The following users are not ready. Do you want to continue generating a game?\n\nYou"
    )
    mock_warning.assert_not_awaited()
    mock_generate_layout.assert_not_called()
    window.game_session_api.prepare_to_upload_layout.assert_not_called()


async def test_check_dangerous_presets_incompatible(window: MultiplayerSessionWindow, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    presets = [MagicMock(), MagicMock(), MagicMock()]
    presets[0].settings_incompatible_with_multiworld.return_value = ["Cake"]
    presets[1].settings_incompatible_with_multiworld.return_value = ["Bomb", "Knife"]
    presets[2].settings_incompatible_with_multiworld.return_value = []

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
    message = (
        "The following worlds have settings that are incompatible with Multiworld:\n"
        "\nCrazy Person: Cake"
        "\nWorld 2: Bomb, Knife"
        "\n\nDo you want to continue?"
    )
    mock_warning.assert_awaited_once_with(window, "Incompatible preset", message)
    assert not result


async def test_check_dangerous_presets_impossible(window: MultiplayerSessionWindow, mocker):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = QtWidgets.QMessageBox.StandardButton.No

    presets = [MagicMock(), MagicMock(), MagicMock()]
    presets[0].settings_incompatible_with_multiworld.return_value = []
    presets[1].settings_incompatible_with_multiworld.return_value = []
    presets[2].settings_incompatible_with_multiworld.return_value = []
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
    message = (
        "The following worlds have settings that can cause an impossible game:\n"
        "\nCrazy Person: Cake"
        "\nWorld 2: Bomb, Knife"
        "\n\nDo you want to continue?"
    )
    mock_warning.assert_awaited_once_with(
        window,
        "Dangerous preset",
        message,
        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
    )
    assert not result


async def test_copy_permalink_is_admin(window: MultiplayerSessionWindow, mocker):
    mock_set_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window.game_session_api.request_permalink = AsyncMock(return_value="<permalink>")

    # Run
    await window.copy_permalink()

    # Assert
    window.game_session_api.request_permalink.assert_awaited_once_with()
    execute_dialog.assert_awaited_once()
    assert execute_dialog.call_args.args[0].textValue() == "<permalink>"
    mock_set_clipboard.assert_called_once_with("<permalink>")


async def test_copy_permalink_not_admin(window: MultiplayerSessionWindow, mocker):
    mock_set_clipboard: MagicMock = mocker.patch("randovania.gui.lib.common_qt_lib.set_clipboard")
    execute_dialog: AsyncMock = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    window.game_session_api.request_permalink = AsyncMock(return_value=None)

    # Run
    await window.copy_permalink()

    # Assert
    window.game_session_api.request_permalink.assert_awaited_once_with()
    execute_dialog.assert_not_awaited()
    mock_set_clipboard.assert_not_called()


@pytest.mark.parametrize("end_state", ["reject", "wrong_count", "abort", "import"])
async def test_import_permalink(window: MultiplayerSessionWindow, end_state, mocker: MockerFixture):
    mock_permalink_dialog = mocker.patch("randovania.gui.multiplayer_session_window.PermalinkDialog")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    execute_dialog.return_value = (
        QtWidgets.QDialog.DialogCode.Rejected if end_state == "reject" else QtWidgets.QDialog.DialogCode.Accepted
    )
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_warning.return_value = (
        QtWidgets.QMessageBox.StandardButton.No if end_state == "abort" else QtWidgets.QMessageBox.StandardButton.Yes
    )

    permalink = mock_permalink_dialog.return_value.get_permalink_from_field.return_value
    permalink.parameters.world_count = 2 - (end_state == "wrong_count")
    permalink.parameters.presets = [MagicMock(), MagicMock()]
    permalink.parameters.presets[0].is_same_configuration.return_value = False
    game_mock = MagicMock()
    game_mock.data.long_name = "Foo"
    permalink.parameters.presets[0].game = game_mock
    permalink.parameters.presets[1].game = game_mock

    session = MagicMock()
    session.worlds = [MagicMock(), MagicMock()]
    session.allowed_games = [game_mock]

    window._session = session
    window.generate_game_with_permalink = AsyncMock()
    window.game_session_api.replace_preset_for = AsyncMock()

    # Run
    await window.import_permalink()

    # Assert
    execute_dialog.assert_awaited_once_with(mock_permalink_dialog.return_value)

    if end_state == "reject":
        mock_warning.assert_not_awaited()
        window.generate_game_with_permalink.assert_not_awaited()
        return

    if end_state == "wrong_count":
        mock_warning.assert_awaited_once_with(window, "Incompatible permalink", ANY)
    else:
        mock_warning.assert_awaited_once_with(
            window, "Different presets", ANY, ANY, QtWidgets.QMessageBox.StandardButton.No
        )

    if end_state == "import":
        window.game_session_api.replace_preset_for.assert_has_awaits(
            [
                call(world.id, VersionedPreset.with_preset(preset))
                for world, preset in zip2(session.worlds, permalink.parameters.presets)
            ]
        )
        window.generate_game_with_permalink.assert_awaited_once_with(permalink, retries=None)
    else:
        window.generate_game_with_permalink.assert_not_awaited()
        window.game_session_api.replace_preset_for.assert_not_awaited()


async def test_import_permalink_unsupported_games(window: MultiplayerSessionWindow, mocker: MockerFixture):
    mock_permalink_dialog = mocker.patch("randovania.gui.multiplayer_session_window.PermalinkDialog")
    execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
    execute_dialog.return_value = QtWidgets.QDialog.DialogCode.Accepted
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mocker.patch.object(window, "_on_close_event", AsyncMock())

    unsupported_preset = MagicMock()
    unsupported_preset.game.data.defaults_available_in_game_sessions = False
    unsupported_preset.game.data.long_name = "FooBar's Adventure"

    unsupported_preset_2 = MagicMock()
    unsupported_preset_2.game.data.defaults_available_in_game_sessions = False
    unsupported_preset_2.game.data.long_name = "FooBar's Revenge"

    supported_preset = MagicMock()
    supported_preset.game = MagicMock()
    supported_preset.game.data = MagicMock()
    supported_preset.game.data.defaults_available_in_game_sessions = True
    supported_preset.game.data.long_name = "Return of FooBar"

    session = MagicMock()
    session.worlds = [MagicMock(), MagicMock()]
    session.allowed_games = [supported_preset.game]
    window._session = session

    permalink = mock_permalink_dialog.return_value.get_permalink_from_field.return_value
    permalink.parameters.presets = [supported_preset, unsupported_preset, unsupported_preset_2]

    # Run
    await window.import_permalink()

    # Assert
    execute_dialog.assert_awaited_once_with(mock_permalink_dialog.return_value)
    mock_warning.assert_awaited_once_with(
        window, "Invalid layout", "Unsupported games: FooBar's Adventure, FooBar's Revenge"
    )


@pytest.mark.parametrize("end_state", ["reject", "wrong_count", "import"])
async def test_import_layout(
    window: MultiplayerSessionWindow, end_state, mocker: MockerFixture, prepare_to_upload_layout
):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_load_layout = mocker.patch(
        "randovania.gui.lib.layout_loader.prompt_and_load_layout_description", new_callable=AsyncMock
    )
    layout = mock_load_layout.return_value
    layout.save_to_file = MagicMock()
    layout.as_json = MagicMock()
    if end_state == "reject":
        mock_load_layout.return_value = None

    uploader: AsyncMock = prepare_to_upload_layout.__aenter__.return_value
    window.game_session_api.prepare_to_upload_layout = MagicMock(return_value=prepare_to_upload_layout)

    preset = MagicMock()
    preset.is_same_configuration.return_value = True
    layout.generator_parameters.world_count = 2 + (end_state == "wrong_count")
    layout.generator_parameters.presets = [preset, preset]
    layout.generator_parameters.get_preset = MagicMock(return_value=preset)

    session = MagicMock()
    session.worlds = [MagicMock(), MagicMock()]
    session.worlds[0].id = "uid1"
    session.worlds[1].id = "uid2"
    window._session = session
    window.generate_game_with_permalink = AsyncMock()

    window.game_session_api.create_unclaimed_world = AsyncMock()
    window.game_session_api.replace_preset_for = AsyncMock()

    # Run
    await window.import_layout()

    # Assert
    mock_load_layout.assert_awaited_once_with(window)

    if end_state == "wrong_count":
        window.game_session_api.create_unclaimed_world.assert_awaited_once_with("World 3", ANY)
        assert window.game_session_api.create_unclaimed_world.await_args[0][1]._preset is preset
        mock_warning.assert_awaited_once_with(
            window, "Temporary error", "New worlds created to fit the imported game file. Please import it again."
        )
    else:
        mock_warning.assert_not_awaited()
        window.game_session_api.create_unclaimed_world.assert_not_awaited()

    if end_state == "import":
        window.game_session_api.prepare_to_upload_layout.assert_called_once_with(["uid1", "uid2"])
        window.game_session_api.replace_preset_for.assert_has_awaits(
            [call(world.id, VersionedPreset.with_preset(preset)) for world in session.worlds]
        )
        uploader.assert_awaited_once_with(layout)
    else:
        window.game_session_api.prepare_to_upload_layout.assert_not_called()


async def test_import_layout_unsupported_games(window: MultiplayerSessionWindow, mocker: MockerFixture):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_load_layout = mocker.patch(
        "randovania.gui.lib.layout_loader.prompt_and_load_layout_description", new_callable=AsyncMock
    )
    mocker.patch.object(window, "_on_close_event", AsyncMock())

    unsupported_preset = MagicMock()
    unsupported_preset.game.data.defaults_available_in_game_sessions = False
    unsupported_preset.game.data.long_name = "FooBar's Adventure"

    unsupported_preset_2 = MagicMock()
    unsupported_preset_2.game.data.defaults_available_in_game_sessions = False
    unsupported_preset_2.game.data.long_name = "FooBar's Revenge"

    supported_preset = MagicMock()
    supported_preset.game.data.defaults_available_in_game_sessions = True
    supported_preset.game.data.long_name = "Return of FooBar"

    session = MagicMock()
    session.worlds = [MagicMock(), MagicMock()]
    session.allowed_games = [supported_preset.game]
    window._session = session

    layout = MagicMock()
    layout.all_presets = [supported_preset, unsupported_preset, unsupported_preset_2]
    mock_load_layout.return_value = layout

    # Run
    await window.import_layout()

    # Assert
    mock_load_layout.assert_awaited_once_with(window)
    # Assert
    mock_warning.assert_awaited_once_with(
        window, "Invalid layout", "Unsupported games: FooBar's Adventure, FooBar's Revenge"
    )


@pytest.mark.parametrize("already_kicked", [True, False])
async def test_on_kicked(skip_qtbot, window: MultiplayerSessionWindow, mocker, already_kicked):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    window.network_client.listen_to_session = AsyncMock()
    window._session = MagicMock()
    window._already_kicked = already_kicked
    window.close = MagicMock(return_value=None)

    # Run
    await window._on_kicked()
    if not already_kicked:
        skip_qtbot.waitUntil(window.close)

    # Assert
    if already_kicked:
        window.network_client.listen_to_session.assert_not_awaited()
        mock_warning.assert_not_awaited()
        window.close.assert_not_called()
    else:
        window.network_client.listen_to_session.assert_awaited_once_with(window._session.id, False)
        mock_warning.assert_awaited_once()
        window.close.assert_called_once_with()


async def test_game_export_listener(
    window: MultiplayerSessionWindow, mocker: pytest_mock.MockerFixture, echoes_game_description, preset_manager
):
    mock_execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        new_callable=AsyncMock,
        return_value=QtWidgets.QDialog.DialogCode.Accepted,
    )
    mock_preset_from = mocker.patch("randovania.layout.versioned_preset.VersionedPreset.from_str")

    game = mock_preset_from.return_value.game
    window._session = MagicMock()
    window._session.name = "Session'x Name 51?"
    world = MultiplayerWorld(
        id=uuid.uuid4(),
        name="W1",
        preset_raw=json.dumps(preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json),
    )
    window._session.get_world.return_value = world
    window._session.worlds = [world]
    window.network_client.session_admin_player = AsyncMock()

    patch_data = MagicMock()
    game.exporter.is_busy = False

    # Run
    await window.game_export_listener(world.id, patch_data)

    # Assert
    window._session.get_world.assert_called_once_with(world.id)
    mock_preset_from.assert_called_once_with(world.preset_raw)

    game.gui.export_dialog.assert_called_once_with(
        window._options,
        patch_data,
        "Sessionx Name 51 - W1",
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
async def test_on_close_event(window: MultiplayerSessionWindow, mocker, is_member):
    # Setup
    super_close_event = mocker.patch("PySide6.QtWidgets.QMainWindow.closeEvent")
    event = MagicMock()
    window._session = MagicMock()
    window._session.users = [window.network_client.current_user.id] if is_member else []
    window.network_client.listen_to_session = AsyncMock()
    window.network_client.connection_state.is_disconnected = False

    # Run
    await window._on_close_event(event)
    event.ignore.assert_not_called()
    super_close_event.assert_called_once_with(event)

    if is_member:
        window.network_client.listen_to_session.assert_awaited_once_with(window._session.id, False)
    else:
        window.network_client.listen_to_session.assert_not_awaited()


async def test_update_session_audit_log(window: MultiplayerSessionWindow):
    window._session = MagicMock()
    log = MultiplayerSessionAuditLog(
        session_id=window._session.id,
        entries=[
            MultiplayerSessionAuditEntry("You", f"Did something for the {i}-th time.", datetime.datetime.now())
            for i in range(50)
        ],
    )
    scrollbar = window.tab_audit.verticalScrollBar()

    # Run
    window.update_session_audit_log(log)
    assert scrollbar.value() == scrollbar.maximum()

    assert window.audit_item_model.item(0, 0).text() == "You"
    assert window.audit_item_model.item(0, 1).text() == "Did something for the 0-th time."

    window.tab_audit.scrollToTop()
    window.update_session_audit_log(log)
    assert scrollbar.value() == scrollbar.minimum()


async def test_on_close_item_tracker(window: MultiplayerSessionWindow, mocker: pytest_mock.MockerFixture):
    world_uid = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    user_id = 10
    mocked_tracker = MagicMock()
    window.tracker_windows[(world_uid, user_id)] = mocked_tracker
    window.network_client.world_track_inventory = AsyncMock()

    the_coroutine = None

    def run(c, loop):
        nonlocal the_coroutine
        the_coroutine = c
        assert loop == asyncio.get_event_loop()

    mocker.patch("asyncio.run_coroutine_threadsafe", side_effect=run)

    # Run
    window._on_close_item_tracker(world_uid, user_id)
    assert the_coroutine is not None
    await the_coroutine

    # Assert
    assert window.tracker_windows == {}
    window.network_client.world_track_inventory.assert_awaited_once_with(world_uid, user_id, False)


async def test_track_world_listener_existing_window(window: MultiplayerSessionWindow):
    world_uid = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    user_id = 10
    mocked_tracker = MagicMock()
    window.tracker_windows[(world_uid, user_id)] = mocked_tracker

    # Run
    await window.track_world_listener(world_uid, user_id)

    # Assert
    mocked_tracker.raise_.assert_called_once_with()


async def test_track_world_listener_create(
    window: MultiplayerSessionWindow, mocker: pytest_mock.MockerFixture, preset_manager
):
    world_uid = uuid.UUID("53308c10-c283-4be5-b5d2-1761c81a871b")
    user_id = 10
    mock_popup_window = mocker.patch("randovania.gui.multiplayer_session_window.ItemTrackerPopupWindow")

    window.network_client.world_track_inventory = AsyncMock()

    window._session = MagicMock()
    world = window._session.get_world.return_value
    world.preset_raw = json.dumps(preset_manager.default_preset_for_game(RandovaniaGame.METROID_PRIME_ECHOES).as_json)

    # Run
    await window.track_world_listener(world_uid, user_id)

    # Assert
    window._session.get_world.assert_called_once_with(world_uid)
    mock_popup_window.return_value.show.assert_called_once_with()
    assert window.tracker_windows == {(world_uid, user_id): mock_popup_window.return_value}
    window.network_client.world_track_inventory.assert_awaited_once_with(world_uid, user_id, True)


@pytest.mark.parametrize("visibility", list(MultiplayerSessionVisibility) + [None])
async def test_session_visibility_button_clicked(window: MultiplayerSessionWindow, visibility):
    window._session = MagicMock()
    window._session.visibility = visibility
    window.game_session_api.change_visibility = AsyncMock()

    if visibility is None:
        expectation = pytest.raises(RuntimeError, match=f"Unknown session state: {visibility}")
    else:
        expectation = contextlib.nullcontext()

    # Run
    with expectation:
        await window._session_visibility_button_clicked_raw()

    if visibility is not None:
        window.game_session_api.change_visibility.assert_called_once_with(
            MultiplayerSessionVisibility.VISIBLE
            if visibility == MultiplayerSessionVisibility.HIDDEN
            else MultiplayerSessionVisibility.HIDDEN
        )


@pytest.mark.parametrize("accept", [False, True])
@pytest.mark.parametrize("has_actions", [False, True])
async def test_clear_generated_game(
    window: MultiplayerSessionWindow, mocker: pytest_mock.MockerFixture, has_actions, accept
):
    execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.yes_no_prompt", new_callable=AsyncMock, return_value=accept
    )

    window._last_actions = MultiplayerSessionActions(0, [1] if has_actions else [])
    window.game_session_api.clear_generated_game = AsyncMock()

    # Run
    await window.clear_generated_game()

    # Assert
    execute_dialog.assert_awaited_once_with(
        window,
        "Clear generated game?",
        ANY,
        icon=QtWidgets.QMessageBox.Icon.Critical if has_actions else QtWidgets.QMessageBox.Icon.Warning,
    )
    if accept:
        window.game_session_api.clear_generated_game.assert_awaited_once_with()
    else:
        window.game_session_api.clear_generated_game.assert_not_awaited()
