from pathlib import Path

import pytest
import socketio.exceptions
from mock import MagicMock, AsyncMock, call

from randovania.games.game import RandovaniaGame
from randovania.network_client.game_session import GameSessionPickups
from randovania.network_client.network_client import NetworkClient, ConnectionState
from randovania.network_common import connection_headers
from randovania.network_common.admin_actions import SessionAdminGlobalAction, SessionAdminUserAction
from randovania.network_common.error import InvalidSession, RequestTimeout, ServerError


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
async def test_on_connect_restore_timeout(client: NetworkClient):
    # Setup
    client._restore_session = AsyncMock(side_effect=ServerError())
    client._connection_state = ConnectionState.Connecting
    client.disconnect_from_server = AsyncMock()

    # Run
    await client.on_connect()

    # Assert
    assert client.connection_state == ConnectionState.Disconnected
    client.disconnect_from_server.assert_awaited_once_with()


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
                                                headers=connection_headers())


@pytest.mark.asyncio
async def test_session_admin_global(client):
    client._emit_with_result = AsyncMock()
    client._current_game_session_meta = MagicMock()
    client._current_game_session_meta.id = 1234

    # Run
    result = await client.session_admin_global(SessionAdminGlobalAction.CHANGE_ROW, 5)

    # Assert
    assert result == client._emit_with_result.return_value
    client._emit_with_result.assert_awaited_once_with("game_session_admin_session", (1234, "change_row", 5))


@pytest.mark.parametrize("permanent", [False, True])
@pytest.mark.asyncio
async def test_leave_game_session(client: NetworkClient, permanent: bool):
    client._emit_with_result = AsyncMock()
    client._current_game_session_meta = MagicMock()
    client._current_game_session_meta.id = 1234
    client._current_user = MagicMock()
    client._current_user.id = 5678

    # Run
    await client.leave_game_session(permanent)

    # Assert
    calls = [call("disconnect_game_session", 1234)]
    if permanent:
        calls.insert(0, call("game_session_admin_player", (1234, 5678, SessionAdminUserAction.KICK.value, None)))

    client._emit_with_result.assert_has_awaits(calls)

    assert client._current_game_session_meta is None


@pytest.mark.asyncio
async def test_emit_with_result_timeout(client: NetworkClient):
    # Setup
    client._connection_state = ConnectionState.Connected
    client.sio = AsyncMock()
    client.sio.call.side_effect = socketio.exceptions.TimeoutError()

    # Run
    with pytest.raises(RequestTimeout, match="Timeout after "):
        await client._emit_with_result("test_event")


def test_update_timeout_with_increase(client: NetworkClient):
    # Run
    client._update_timeout_with(5.0, False)

    # Assert
    assert client._current_timeout == 40


def test_update_timeout_with_dont_decrease_below_minimum(client: NetworkClient):
    # Setup
    client._current_timeout = 30

    # Run
    client._update_timeout_with(5.0, True)

    # Assert
    assert client._current_timeout == 30


def test_update_timeout_with_decrease_on_success(client: NetworkClient):
    # Setup
    client._current_timeout = 50

    # Run
    client._update_timeout_with(5.0, True)

    # Assert
    assert client._current_timeout == 40


@pytest.mark.asyncio
async def test_refresh_received_pickups(client: NetworkClient, corruption_game_description, mocker):
    db = corruption_game_description.resource_database

    data = {
        "game": RandovaniaGame.METROID_PRIME_CORRUPTION.value,
        "pickups": [
            {"provider_name": "Message A", "pickup": 'VtI6Bb3p'},
            {"provider_name": "Message B", "pickup": 'VtI6Bb3y'},
            {"provider_name": "Message C", "pickup": 'VtI6Bb3*'},
        ]
    }

    pickups = [MagicMock(), MagicMock(), MagicMock()]
    mock_decode = mocker.patch("randovania.network_client.network_client._decode_pickup", side_effect=pickups)

    # Run
    await client._on_game_session_pickups_update_raw(data)

    # Assert
    assert client._current_game_session_pickups == GameSessionPickups(
        game=RandovaniaGame.METROID_PRIME_CORRUPTION,
        pickups=(
            ("Message A", pickups[0]),
            ("Message B", pickups[1]),
            ("Message C", pickups[2]),
        )
    )
    mock_decode.assert_has_calls([call('VtI6Bb3p', db), call('VtI6Bb3y', db), call('VtI6Bb3*', db)])
