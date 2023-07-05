import logging
import uuid
from unittest.mock import AsyncMock, MagicMock, ANY

import pytest
from PySide6 import QtWidgets
from pytest_mock import MockerFixture

from randovania.gui.lib import multiplayer_session_api
from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import error, admin_actions


@pytest.mark.parametrize("exception", [
    None, error.NotAuthorizedForActionError(), error.UserNotAuthorizedToUseServerError(),
    error.ServerError(), error.NotLoggedInError(), error.RequestTimeoutError("timeout"),
    error.InvalidActionError("not this"),
    error.UnsupportedClientError("Not nice<br />An Error"),
    UnableToConnect("No connect"),
    error.WorldDoesNotExistError(),
])
async def test_handle_network_errors(skip_qtbot, mocker: MockerFixture, exception):
    mock_warning = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)

    root = QtWidgets.QWidget()
    skip_qtbot.add_widget(root)

    api = MagicMock()
    api.widget_root = root

    fn = AsyncMock(side_effect=exception)
    arg = MagicMock()

    # Run
    wrapped = multiplayer_session_api.handle_network_errors(fn)
    result = await wrapped(api, arg)

    # Assert
    if exception is None:
        assert result == fn.return_value
        mock_warning.assert_not_called()
    else:
        assert result is None
        mock_warning.assert_awaited_once_with(root, ANY, ANY)


@pytest.fixture()
def session_api(skip_qtbot):
    network_client = MagicMock()
    network_client.server_call = AsyncMock()
    root = QtWidgets.QWidget()
    skip_qtbot.addWidget(root)

    api = MultiplayerSessionApi(network_client, 1234)
    api.logger.setLevel(logging.DEBUG)
    api.widget_root = root
    return api


async def test_replace_preset_for(session_api, caplog, preset_manager):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.replace_preset_for(uid, preset_manager.default_preset)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        (1234,
         admin_actions.SessionAdminGlobalAction.CHANGE_WORLD.value,
         ('487fd145-d590-4984-b761-056974ce7d6d', preset_manager.default_preset.as_json)),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Replacing preset for 487fd145-d590-4984-b761-056974ce7d6d with Starter Preset')
    ]


async def test_claim_world(session_api, caplog):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.claim_world_for(uid, 20)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        (1234, 20,
         admin_actions.SessionAdminUserAction.CLAIM.value,
         '487fd145-d590-4984-b761-056974ce7d6d'),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Claiming 487fd145-d590-4984-b761-056974ce7d6d for 20')
    ]


async def test_unclaim_world(session_api, caplog):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.unclaim_world(uid, 20)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        (1234, 20,
         admin_actions.SessionAdminUserAction.UNCLAIM.value,
         '487fd145-d590-4984-b761-056974ce7d6d'),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Unclaiming 487fd145-d590-4984-b761-056974ce7d6d from 20')
    ]


async def test_rename_world(session_api, caplog):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.rename_world(uid, "the name")

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        (1234,
         admin_actions.SessionAdminGlobalAction.RENAME_WORLD.value,
         ('487fd145-d590-4984-b761-056974ce7d6d', "the name")),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Renaming world 487fd145-d590-4984-b761-056974ce7d6d to the name')
    ]


async def test_delete_world(session_api, caplog):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.delete_world(uid)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        (1234,
         admin_actions.SessionAdminGlobalAction.DELETE_WORLD.value,
         '487fd145-d590-4984-b761-056974ce7d6d'),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Deleting world 487fd145-d590-4984-b761-056974ce7d6d')
    ]


async def test_create_new_world(session_api, caplog, preset_manager):
    # Run
    await session_api.create_new_world("a friend", preset_manager.default_preset, 50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        (1234, 50,
         admin_actions.SessionAdminUserAction.CREATE_WORLD_FOR.value,
         ("a friend", preset_manager.default_preset.as_json)),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         "[Session 1234] Creating world named 'a friend' with Starter Preset for 50")
    ]


async def test_create_patcher_file(session_api, caplog):
    uid = uuid.UUID('487fd145-d590-4984-b761-056974ce7d6d')

    # Run
    await session_api.create_patcher_file(uid, {})

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        (1234,
         admin_actions.SessionAdminGlobalAction.CREATE_PATCHER_FILE.value,
         ('487fd145-d590-4984-b761-056974ce7d6d', {})),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         '[Session 1234] Requesting patcher file for 487fd145-d590-4984-b761-056974ce7d6d')
    ]


async def test_kick_player(session_api, caplog):
    # Run
    await session_api.kick_player(50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        (1234, 50,
         admin_actions.SessionAdminUserAction.KICK.value,
         None),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         "[Session 1234] Kicking player 50")
    ]


async def test_switch_admin(session_api, caplog):
    # Run
    await session_api.switch_admin(50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        (1234, 50,
         admin_actions.SessionAdminUserAction.SWITCH_ADMIN.value,
         None),
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         "[Session 1234] Switching admin-ness of 50")
    ]


async def test_request_session_update(session_api, caplog):
    # Run
    await session_api.request_session_update()

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_request_session_update",
        1234,
    )
    assert caplog.record_tuples == [
        ('MultiplayerSessionApi', logging.INFO,
         "[Session 1234] Requesting updated session data")
    ]
