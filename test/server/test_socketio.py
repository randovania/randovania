from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock

import pytest
import socketio.exceptions

from randovania.network_common import connection_headers, error
from randovania.network_common.signals.server_signals import server_signal
from test.server.sio_test_client import SocketIOTestClient

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture(name="sio_test_client")
async def sio_test_client_fixture(test_client):
    client = SocketIOTestClient(test_client.sa.sio)

    headers = {"HTTP_{}".format(k.upper().replace("-", "_")): v for k, v in connection_headers().items()}
    await client.connect(headers=headers)
    return client


@pytest.mark.parametrize(
    ("has_headers", "context"),
    [
        (False, pytest.raises(socketio.exceptions.ConnectionRefusedError, match="unknown client version")),
        (True, nullcontext()),
    ],
)
async def test_sio_connect_version_header(
    test_client, has_headers: bool, context: AbstractContextManager, is_dev_version
):
    client = SocketIOTestClient(test_client.sa.sio)

    headers = {}
    if has_headers:
        if not is_dev_version:
            headers = {"HTTP_{}".format(k.upper().replace("-", "_")): v for k, v in connection_headers().items()}
        headers["HTTP_X_RANDOVANIA_VERSION"] = "0.0.0"

    with context:
        await client.connect(headers=headers)

    assert client.is_connected() == has_headers


@pytest.mark.parametrize("client_version_check_rval", [None, "An error"])
async def test_sio_connect_client_check_error(test_client, mocker: MockerFixture, client_version_check_rval):
    mocker.patch(
        "randovania.server.client_check.check_client_version",
        return_value=client_version_check_rval,
    )
    mocker.patch(
        "randovania.server.client_check.check_client_headers",
        return_value="Another error",
    )
    mocker.patch("randovania.is_dev_version", return_value=False)

    client = SocketIOTestClient(test_client.sa.sio)
    headers = {
        "HTTP_X_RANDOVANIA_VERSION": "0.0.0",
    }

    expected = client_version_check_rval or "Another error"
    with pytest.raises(socketio.exceptions.ConnectionRefusedError, match=expected):
        await client.connect(headers=headers)


@pytest.mark.parametrize(
    ("side_effect", "rval"),
    [
        ([{"foo": 12345}], {"result": {"foo": 12345}}),  # success
        (error.NotLoggedInError(), error.NotLoggedInError().as_json),  # network error
        (RuntimeError("something happened"), error.ServerError().as_json),  # exception
    ],
)
async def test_on_success(side_effect: Any, rval: dict, test_client, sio_test_client):
    # Setup
    custom = server_signal("custom")(AsyncMock(side_effect=side_effect))
    custom.register(test_client.sa, custom.fn)

    # Run
    result = await sio_test_client.emit("custom", callback=True)

    # Assert
    custom.fn.assert_awaited_once_with(test_client.sa, sio_test_client.sid)
    assert result == rval
