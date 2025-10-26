from __future__ import annotations

import logging
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.network_common import error
from randovania.server import database
from randovania.server.server_app import EnforceDiscordRole, ServerLoggingFormatter

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(name="sid")
def sid_fixture() -> str:
    return "12345"


@pytest.mark.parametrize(
    ("rval", "create_user", "context"),
    [
        ({"user-id": 1234}, True, nullcontext()),  # user exists (success)
        ({"user-id": 1234}, False, pytest.raises(error.InvalidSessionError)),  # unknown user
        ({}, False, pytest.raises(error.NotLoggedInError)),  # not logged in
    ],
)
async def test_get_current_user(
    rval: dict, create_user: bool, context: AbstractContextManager, test_client, sid, clean_database
):
    test_client.sa.sio.get_session = AsyncMock(return_value=rval)
    if create_user:
        user = database.User.create(id=1234, name="Someone")

    # Run
    with context:
        result = await test_client.sa.get_current_user(sid)

    # Assert
    if create_user:
        assert result == user


async def test_store_world_in_session(test_client, sid):
    session = {}
    test_client.sa.sio.session = MagicMock()
    test_client.sa.sio.session.return_value.__aenter__.return_value = session

    world = MagicMock()
    world.id = 1234

    # Run
    await test_client.sa.store_world_in_session(sid, world)

    # Assert
    assert session == {"worlds": [1234]}


async def test_remove_world_from_session(test_client, sid):
    session = {"worlds": [1234]}
    test_client.sa.sio.session = MagicMock()
    test_client.sa.sio.session.return_value.__aenter__.return_value = session

    world = MagicMock()
    world.id = 1234

    # Run
    await test_client.sa.remove_world_from_session(sid, world)

    # Assert
    assert session == {"worlds": []}


@pytest.mark.parametrize("valid", [False, True])
async def test_verify_user(server_app, mocker: MockerFixture, valid):
    # Setup
    mock_session = MagicMock()
    mock_session.headers = {}
    mock_session.get = MagicMock()
    mock_session.get.return_value.__aenter__.return_value.json.return_value = {"roles": ["5678" if valid else "67689"]}

    mock_session_factory = mocker.patch("aiohttp.ClientSession")
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    server_app.configuration["server_config"]["enforce_role"] = {
        "guild_id": 1234,
        "role_id": 5678,
        "token": "da_token",
    }

    # Run
    async with EnforceDiscordRole.lifespan(server_app.app) as enforce:
        assert enforce is not None
        result = await enforce.verify_user("2345")

    # Assert
    assert result == valid
    mock_session.get.assert_called_once_with("https://discordapp.com/api/guilds/1234/members/2345")
    mock_session.get.return_value.__aenter__.assert_awaited_once_with()
    mock_session.get.return_value.__aexit__.assert_awaited_once_with(None, None, None)
    mock_session.get.return_value.__aenter__.return_value.json.assert_awaited_once_with()
    assert mock_session.headers == {
        "Authorization": "Bot da_token",
    }


@pytest.mark.parametrize("expected", [False, True])
async def test_ensure_in_room(test_client, sid, expected):
    test_client.sa.sio.rooms = MagicMock(return_value=[] if expected else ["the_room"])
    test_client.sa.sio.enter_room = AsyncMock()

    # Run
    result = await test_client.sa.ensure_in_room(sid, "the_room")

    # Assert
    test_client.sa.sio.rooms.assert_called_once_with(sid, namespace="/")
    test_client.sa.sio.enter_room.assert_awaited_once_with(sid, "the_room", namespace="/")
    assert result is expected


async def test_fernet(server_app):
    encrpyted_value = (
        b"gAAAAABfSh6fY4FOiqfGWMHXdE9A4uNVEu5wfn8BAsgP8EZ0-f-lqbYDqYzdiblhT5xhk-wMmG8sOLgKNN-dUaiV7n6JCydn7Q=="
    )
    assert server_app.fernet_encrypt.decrypt(encrpyted_value) == b"banana"


def test_custom_formatter():
    record = logging.LogRecord("Name", logging.DEBUG, "path", 10, "the msg", (), None)

    x = ServerLoggingFormatter(
        "%(levelprefix)s %(context)s [%(who)s] in %(where)s: %(msg)s",
        use_colors=False,
    )
    result = x.formatMessage(record)

    assert result == "DEBUG:    Free [None] in None: the msg"
