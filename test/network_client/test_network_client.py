from pathlib import Path

import pytest
from mock import MagicMock, AsyncMock, call

import randovania
from randovania.network_client.network_client import NetworkClient, ConnectionState
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.error import InvalidSession


@pytest.fixture(name="client")
def _client(tmpdir):
    return NetworkClient(Path(tmpdir), {"server_address": "http://localhost:5000"})


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

    async def connect(*args, **kwargs):
        client._waiting_for_on_connect.set_result(True)

    client.sio = MagicMock()
    client.sio.connect = AsyncMock(side_effect=connect)
    client.sio.connected = False

    # Run
    await client.connect_to_server()

    # Assert
    assert client.connection_state == ConnectionState.Connecting
    client.sio.connect.assert_awaited_once_with("http://localhost:5000",
                                                socketio_path="/path",
                                                transports=["websocket"],
                                                headers={"X-Randovania-Version": randovania.VERSION})


@pytest.mark.asyncio
async def test_session_admin_global(client):
    client._emit_with_result = AsyncMock()
    client._current_game_session = MagicMock()
    client._current_game_session.id = 1234

    # Run
    result = await client.session_admin_global(SessionAdminGlobalAction.CHANGE_ROW, 5)

    # Assert
    assert result == client._emit_with_result.return_value
    client._emit_with_result.assert_awaited_once_with("game_session_admin_session", (1234, "change_row", 5))


@pytest.mark.parametrize("permanent", [False, True])
@pytest.mark.asyncio
async def test_leave_game_session(client: NetworkClient, permanent: bool):
    client._emit_with_result = AsyncMock()
    client._current_game_session = MagicMock()
    client._current_game_session.id = 1234
    client._current_user = MagicMock()
    client._current_user.id = 5678
    client._last_self_update = "foobar"

    # Run
    await client.leave_game_session(permanent)

    # Assert
    calls = [call("disconnect_game_session", 1234)]
    if permanent:
        calls.insert(0, call("game_session_admin_player", (1234, 5678, SessionAdminUserAction.KICK.value, None)))

    client._emit_with_result.assert_has_awaits(calls)

    assert client._current_game_session is None
    assert client._last_self_update is None
