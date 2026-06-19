from __future__ import annotations

import re
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from socketio import AsyncClient, AsyncServer

from randovania.network_common.signals.client_signals import ClientSignal, client_signal
from randovania.network_common.signals.server_signals import ServerSignal, server_signal

if TYPE_CHECKING:
    from randovania.server.server_app import ServerApp


@pytest.fixture
def client_test_signal() -> ClientSignal[[str]]:
    @client_signal("client_test")
    async def ClientTestSignal(data: str) -> None: ...

    return ClientTestSignal


@pytest.fixture
def server_test_signal() -> ServerSignal[[str], str]:
    @server_signal("server_test")
    async def ServerTestSignal(sa: ServerApp, sid: str, data: str) -> str:
        raise NotImplementedError

    return ServerTestSignal


@pytest.fixture
def client() -> MagicMock:
    result = MagicMock()
    result.server_call = AsyncMock()
    result.sio = MagicMock(spec=AsyncClient)
    return result


@pytest.fixture
def server() -> MagicMock:
    result = MagicMock()
    result.sio = MagicMock(spec=AsyncServer)
    return result


def test_direct_signal_call(client_test_signal, server_test_signal):
    client_match = (
        r"Cannot call ClientSignal ClientTestSignal directly. "
        r"Did you mean to call ClientTestSignal.emit() instead?"
    )
    with pytest.raises(TypeError, match=re.escape(client_match)):
        client_test_signal("foo")

    server_match = (
        r"Cannot call ServerSignal ServerTestSignal directly. "
        r"Did you mean to call ServerTestSignal.call_server() instead?"
    )
    with pytest.raises(TypeError, match=re.escape(server_match)):
        server_test_signal("bar")


async def test_client_register_and_emit(client_test_signal, client, server):
    callback = AsyncMock()

    client_test_signal.register(client.sio, callback)
    await client_test_signal.emit(server)("foo")

    client.sio.on.assert_called_once_with("client_test", callback)
    server.sio.emit.assert_awaited_once_with("client_test", "foo", to=None, room=None, namespace=None)


async def test_server_register_and_call(server_test_signal, client, server):
    callback = AsyncMock()

    server_test_signal.register(server, callback)
    await server_test_signal.call_server(client)("bar")

    server.on.assert_called_once_with("server_test", callback, None, with_header_check=False)
    client.server_call.assert_awaited_once_with("server_test", "bar", namespace=None, handle_invalid_session=True)
