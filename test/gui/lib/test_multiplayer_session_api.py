from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib import multiplayer_session_api
from randovania.gui.lib.multiplayer_session_api import MultiplayerSessionApi
from randovania.network_client.network_client import UnableToConnect
from randovania.network_common import admin_actions, error
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    "exception",
    [
        None,
        error.NotAuthorizedForActionError(),
        error.UserNotAuthorizedToUseServerError(),
        error.ServerError(),
        error.NotLoggedInError(),
        error.RequestTimeoutError("timeout"),
        error.InvalidActionError("not this"),
        error.UnsupportedClientError("Not nice<br />An Error"),
        UnableToConnect("No connect"),
        error.WorldDoesNotExistError(),
    ],
)
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


async def test_rename_session(session_api, caplog, preset_manager):
    # Run
    await session_api.rename_session("New Name")

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CHANGE_TITLE.value,
            "New Name",
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Renaming session to New Name")
    ]


async def test_change_password(session_api, caplog, preset_manager):
    # Run
    await session_api.change_password("New Password")

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CHANGE_PASSWORD.value,
            "New Password",
        ],
    )
    assert caplog.record_tuples == [("MultiplayerSessionApi", logging.INFO, "[Session 1234] Changing password")]


async def test_duplicate_session(session_api, caplog, preset_manager):
    # Run
    await session_api.duplicate_session("New Name")

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [1234, admin_actions.SessionAdminGlobalAction.DUPLICATE_SESSION.value, "New Name"],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Duplicating session as New Name")
    ]


@pytest.mark.parametrize("visibility", MultiplayerSessionVisibility)
async def test_change_visibility(session_api, caplog, visibility):
    # Run
    await session_api.change_visibility(visibility)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CHANGE_VISIBILITY.value,
            visibility.value,
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, f"[Session 1234] Setting visibility to {visibility}")
    ]


async def test_abort_generation(session_api, caplog, preset_manager):
    # Run
    await session_api.abort_generation()

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [1234, admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION.value, []],
    )
    assert caplog.record_tuples == [("MultiplayerSessionApi", logging.INFO, "[Session 1234] Aborting generation")]


async def test_upload_layout(session_api, caplog, preset_manager):
    layout = MagicMock()

    # Run
    await session_api._upload_layout(layout)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [1234, admin_actions.SessionAdminGlobalAction.CHANGE_LAYOUT_DESCRIPTION.value, layout.as_binary.return_value],
    )
    layout.as_binary.assert_called_once_with(force_spoiler=True, include_presets=False)
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Uploading a layout description")
    ]


async def test_prepare_to_upload_layout(session_api, caplog, preset_manager):
    mock_server_call = AsyncMock()
    session_api.network_client.server_call = mock_server_call
    world_order = [uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d"), uuid.UUID("ec0cb868-341e-4688-89ce-9757e003b143")]

    # Run
    async with session_api.prepare_to_upload_layout(world_order) as context:
        # Assert
        mock_server_call.assert_called_once_with(
            "multiplayer_admin_session",
            [
                1234,
                admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION.value,
                ["487fd145-d590-4984-b761-056974ce7d6d", "ec0cb868-341e-4688-89ce-9757e003b143"],
            ],
        )
        assert caplog.record_tuples == [
            ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Marking session with generation in progress")
        ]

        assert context == session_api._upload_layout

        mock_server_call.reset_mock()
        caplog.clear()

    mock_server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [1234, admin_actions.SessionAdminGlobalAction.UPDATE_LAYOUT_GENERATION.value, []],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Clearing generation in progress")
    ]


async def test_replace_preset_for(session_api, caplog, preset_manager):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.replace_preset_for(uid, preset_manager.default_preset)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CHANGE_WORLD.value,
            "487fd145-d590-4984-b761-056974ce7d6d",
            preset_manager.default_preset.as_bytes(),
        ],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Replacing preset for 487fd145-d590-4984-b761-056974ce7d6d with Starter Preset",
        )
    ]


async def test_claim_world(session_api, caplog):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.claim_world_for(uid, 20)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [1234, 20, admin_actions.SessionAdminUserAction.CLAIM.value, "487fd145-d590-4984-b761-056974ce7d6d"],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Claiming 487fd145-d590-4984-b761-056974ce7d6d for 20")
    ]


async def test_unclaim_world(session_api, caplog):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.unclaim_world(uid, 20)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [1234, 20, admin_actions.SessionAdminUserAction.UNCLAIM.value, "487fd145-d590-4984-b761-056974ce7d6d"],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Unclaiming 487fd145-d590-4984-b761-056974ce7d6d from 20",
        )
    ]


async def test_rename_world(session_api, caplog):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.rename_world(uid, "the name")

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.RENAME_WORLD.value,
            "487fd145-d590-4984-b761-056974ce7d6d",
            "the name",
        ],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Renaming world 487fd145-d590-4984-b761-056974ce7d6d to the name",
        )
    ]


async def test_delete_world(session_api, caplog):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.delete_world(uid)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.DELETE_WORLD.value,
            "487fd145-d590-4984-b761-056974ce7d6d",
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Deleting world 487fd145-d590-4984-b761-056974ce7d6d")
    ]


async def test_create_new_world(session_api, caplog, preset_manager):
    # Run
    await session_api.create_new_world("a friend", preset_manager.default_preset, 50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [
            1234,
            50,
            admin_actions.SessionAdminUserAction.CREATE_WORLD_FOR.value,
            "a friend",
            preset_manager.default_preset.as_bytes(),
        ],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Creating world named 'a friend' with Starter Preset for 50",
        )
    ]


async def test_create_unclaimed_world(session_api, caplog, preset_manager):
    # Run
    await session_api.create_unclaimed_world("a friend", preset_manager.default_preset)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CREATE_WORLD.value,
            "a friend",
            preset_manager.default_preset.as_bytes(),
        ],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Creating unclaimed world named 'a friend' with Starter Preset",
        )
    ]


async def test_create_patcher_file(session_api, caplog):
    uid = uuid.UUID("487fd145-d590-4984-b761-056974ce7d6d")

    # Run
    await session_api.create_patcher_file(uid, {})

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.CREATE_PATCHER_FILE.value,
            "487fd145-d590-4984-b761-056974ce7d6d",
            {},
        ],
    )
    assert caplog.record_tuples == [
        (
            "MultiplayerSessionApi",
            logging.INFO,
            "[Session 1234] Requesting patcher file for 487fd145-d590-4984-b761-056974ce7d6d",
        )
    ]


async def test_kick_player(session_api, caplog):
    # Run
    await session_api.kick_player(50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [
            1234,
            50,
            admin_actions.SessionAdminUserAction.KICK.value,
        ],
    )
    assert caplog.record_tuples == [("MultiplayerSessionApi", logging.INFO, "[Session 1234] Kicking player 50")]


async def test_switch_admin(session_api, caplog):
    # Run
    await session_api.switch_admin(50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [
            1234,
            50,
            admin_actions.SessionAdminUserAction.SWITCH_ADMIN.value,
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Switching admin-ness of 50")
    ]


@pytest.mark.parametrize("new_state", [False, True])
async def test_set_everyone_can_claim(session_api, caplog, new_state):
    # Run
    await session_api.set_everyone_can_claim(new_state)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.SET_ALLOW_EVERYONE_CLAIM.value,
            new_state,
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, f"[Session 1234] Setting whether everyone can claim to {new_state}")
    ]


async def test_switch_readiness(session_api, caplog):
    # Run
    await session_api.switch_readiness(50)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_player",
        [
            1234,
            50,
            admin_actions.SessionAdminUserAction.SWITCH_READY.value,
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Switching ready-ness of 50")
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
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Requesting updated session data")
    ]


async def test_request_permalink(session_api, caplog):
    # Run
    result = await session_api.request_permalink()

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.REQUEST_PERMALINK.value,
        ],
    )
    assert result is session_api.network_client.server_call.return_value
    assert caplog.record_tuples == [("MultiplayerSessionApi", logging.INFO, "[Session 1234] Requesting permalink")]


@pytest.mark.parametrize("has_result", [False, True])
async def test_request_layout_description(session_api, caplog, mocker: pytest_mock.MockerFixture, has_result):
    # Setup
    mock_from_bytes = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_bytes")
    if not has_result:
        session_api.network_client.server_call.return_value = None

    worlds = [MagicMock(), MagicMock()]

    # Run
    result = await session_api.request_layout_description(worlds)

    # Assert
    session_api.network_client.server_call.assert_called_once_with(
        "multiplayer_admin_session",
        [
            1234,
            admin_actions.SessionAdminGlobalAction.DOWNLOAD_LAYOUT_DESCRIPTION.value,
        ],
    )
    assert caplog.record_tuples == [
        ("MultiplayerSessionApi", logging.INFO, "[Session 1234] Requesting layout description")
    ]
    if has_result:
        assert result is mock_from_bytes.return_value
        mock_from_bytes.assert_called_once_with(
            session_api.network_client.server_call.return_value, presets=[worlds[0].preset, worlds[1].preset]
        )
    else:
        mock_from_bytes.assert_not_called()
        assert result is None
