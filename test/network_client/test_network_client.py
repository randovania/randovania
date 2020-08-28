from pathlib import Path

import pytest
from mock import MagicMock, AsyncMock

import randovania
from randovania.network_client.network_client import NetworkClient, ConnectionState
from randovania.network_common.error import InvalidSession


@pytest.mark.asyncio
async def test_on_connect_no_restore(tmpdir):
    client = NetworkClient(Path(tmpdir), {"server_address": "http://localhost:5000"})

    # Run
    await client.on_connect()

    # Assert
    assert client.connection_state == ConnectionState.ConnectedNotLogged


@pytest.mark.parametrize("valid_session", [False, True])
@pytest.mark.asyncio
async def test_on_connect_restore(tmpdir, valid_session: bool):
    client = NetworkClient(Path(tmpdir), {"server_address": "http://localhost:5000"})
    session_data_path = Path(tmpdir) / "9iwAGnskOkqzo_NZ" / "session_persistence.bin"
    session_data_path.parent.mkdir(parents=True)
    session_data_path.write_bytes(b"foo")

    if valid_session:
        call_result = {"result": {
            "user": {
                "id": 1234,
                "name": "You",
            },
            "encoded_session_b85": b'Ze@30VtI6Ba{'
        }}
    else:
        call_result = InvalidSession().as_json

    client.sio = MagicMock()
    client.sio.call = AsyncMock(return_value=call_result)

    # Run
    await client.on_connect()

    # Assert
    client.sio.call.assert_awaited_once_with("restore_user_session", (b"foo", None), namespace=None, timeout=30)

    if valid_session:
        assert client.connection_state == ConnectionState.Connected
        assert session_data_path.read_bytes() == b"new_bytes"
    else:
        assert client.connection_state == ConnectionState.ConnectedNotLogged
        assert not session_data_path.is_file()


@pytest.mark.asyncio
async def test_connect_to_server(tmpdir):
    # Setup
    client = NetworkClient(Path(tmpdir), {"server_address": "http://localhost:5000",
                                          "socketio_path": "/path"})
    client.sio = MagicMock()
    client.sio.connect = AsyncMock()

    # Run
    await client.connect_to_server()

    # Assert
    assert client.connection_state == ConnectionState.Connecting
    client.sio.connect.assert_awaited_once_with("http://localhost:5000",
                                                socketio_path="/path",
                                                headers={"X-Randovania-Version": randovania.VERSION})
