from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import socketio_handler
from fastapi.testclient import TestClient

import randovania
from randovania.server.database import database_lifespan
from randovania.server.discord_auth import EnforceDiscordRole, EnforceRoleConfiguration, discord_oauth_lifespan
from randovania.server.server_app import ServerApp
from randovania.server.socketio import fastapi_socketio_lifespan

if TYPE_CHECKING:
    import pytest_mock

    from randovania.network_common.configuration import NetworkConfiguration


@pytest.fixture(name="config")
def config_fixture(db_path) -> NetworkConfiguration:
    return {
        "socketio_path": "/prefix/somewhere_evil",
        "discord_client_id": 1234,
        "server_address": "https://somewhere.nice",
        "guest_secret": "s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
        "server_config": {
            "secret_key": "key",
            "discord_client_secret": "5678",
            "fernet_key": "s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
            "database_path": str(db_path),
            "client_version_checking": "strict",
            "socketio_path": "/somewhere_evil",
        },
    }


@pytest.fixture(name="lifespan_sa")
def lifespan_server_app_fixture(config):
    return ServerApp(config)


async def test_discord_auth_lifespan(
    mocker: pytest_mock.MockerFixture,
    lifespan_sa,
):
    mock_discord = MagicMock()
    mock_discord.init = AsyncMock()

    mock_client_session_close = AsyncMock()
    mock_discord.client_session.close = mock_client_session_close

    mock_discord_oauth = mocker.patch(
        "randovania.server.discord_auth.DiscordOAuthClient",
        return_value=mock_discord,
    )

    async with discord_oauth_lifespan(lifespan_sa.app) as discord:
        assert discord == mock_discord
        mock_discord_oauth.assert_called_once_with(
            "1234",
            "5678",
            "",
            ("identify",),
        )
        mock_discord.init.assert_awaited_once_with()

    mock_client_session_close.assert_awaited_once_with()


@pytest.mark.parametrize("state", ["some_state", None])
async def test_discord_oauth_url(lifespan_sa, state):
    mock_request = MagicMock()
    mock_request.url_for.return_value = lifespan_sa.configuration["server_address"]

    async with discord_oauth_lifespan(lifespan_sa.app) as discord:
        result = discord.get_oauth_login_url(mock_request, state)

    base_url = "https://discord.com/api/oauth2/authorize"
    client_param = "?client_id=1234"
    redirect_param = "&redirect_uri=https://somewhere.nice"
    other_params = "&scope=identify&response_type=code"
    state_param = ""
    if state is not None:
        state_param = f"&state={state}"

    assert result == f"{base_url}{client_param}{redirect_param}{other_params}{state_param}"


@pytest.mark.parametrize("enforce", [None])
async def test_enforce_discord_role_lifespan(
    enforce: EnforceRoleConfiguration | None,
    mocker: pytest_mock.MockerFixture,
    lifespan_sa,
):
    lifespan_sa.configuration["server_config"]["enforce_role"] = enforce
    mock_enforce_role = mocker.patch("randovania.server.discord_auth.EnforceDiscordRole.__init__")

    async with EnforceDiscordRole.lifespan(lifespan_sa.app) as enforce_role:
        if enforce is None:
            assert enforce_role is None
            mock_enforce_role.assert_not_called()
        else:
            pass  # TODO: test other cases


async def test_socketio_lifespan(
    mocker: pytest_mock.MockerFixture,
    lifespan_sa,
):
    mock_get_socket_handler = mocker.patch("randovania.server.socketio.get_socket_handler")

    mock_mount_to_app = mocker.patch("socketio_handler.SocketManager.mount_to_app")
    mock_register_handlers = mocker.patch("socketio_handler.SocketManager.register_handlers")

    async with fastapi_socketio_lifespan(lifespan_sa.app) as manager:
        assert isinstance(manager, socketio_handler.SocketManager)

        mock_mount_to_app.assert_called_once_with(
            lifespan_sa.app,
            "/somewhere_evil",
        )

        mock_register_handlers.assert_called_once_with()

        mock_get_socket_handler.assert_called_once_with(lifespan_sa)


async def test_database_lifespan(
    mocker: pytest_mock.MockerFixture,
    lifespan_sa,
    db_path,
):
    async with database_lifespan(lifespan_sa.app):
        assert db_path.exists()


async def test_server_lifespan(
    mocker: pytest_mock.MockerFixture,
    config,
):
    # Setup

    # lifespans
    mock_discord_lifespan = mocker.patch("randovania.server.server_app.discord_oauth_lifespan")
    mock_enforce_lifespan = mocker.patch("randovania.server.server_app.EnforceDiscordRole.lifespan")
    mock_socketio_lifespan = mocker.patch("randovania.server.server_app.fastapi_socketio_lifespan")
    mock_database_lifespan = mocker.patch("randovania.server.server_app.database_lifespan")

    # routing
    mock_multiplayer = mocker.patch("randovania.server.multiplayer.setup_app")
    mock_user_session = mocker.patch("randovania.server.user_session.setup_app")
    mock_async_race = mocker.patch("randovania.server.async_race.setup_app")

    sa = ServerApp(config)

    # Assert
    with TestClient(sa.app) as test_client:
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.text == randovania.VERSION

    # lifespans
    def check_lifespan(lifespan: MagicMock):
        lifespan.assert_called_once_with(sa.app)
        lifespan.return_value.__aenter__.assert_awaited_once_with()
        lifespan.return_value.__aexit__.assert_awaited_once_with(None, None, None)

    check_lifespan(mock_discord_lifespan)
    check_lifespan(mock_enforce_lifespan)
    check_lifespan(mock_socketio_lifespan)
    check_lifespan(mock_database_lifespan)

    # routing
    mock_multiplayer.assert_called_once_with(sa)
    mock_user_session.assert_called_once_with(sa)
    mock_async_race.assert_called_once_with(sa)
