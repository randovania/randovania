from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import aiohttp.client_exceptions
import pytest
import socketio.exceptions

from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.games.game import RandovaniaGame
from randovania.network_client.network_client import ConnectionState, NetworkClient, UnableToConnect, _decode_pickup
from randovania.network_common import connection_headers, remote_inventory
from randovania.network_common.admin_actions import SessionAdminGlobalAction
from randovania.network_common.error import InvalidSessionError, RequestTimeoutError, ServerError
from randovania.network_common.multiplayer_session import MultiplayerWorldPickups, WorldUserInventory

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture()
def client(tmp_path):
    return NetworkClient(tmp_path, {"server_address": "http://localhost:5000"})


async def test_on_connect_no_restore(tmp_path):
    client = NetworkClient(tmp_path, {"server_address": "http://localhost:5000"})

    # Run
    await client.on_connect()

    # Assert
    assert client.connection_state == ConnectionState.ConnectedNotLogged


@pytest.mark.parametrize("valid_session", [False, True])
async def test_on_connect_restore(tmpdir, valid_session: bool):
    client = NetworkClient(Path(tmpdir), {"server_address": "http://localhost:5000"})
    session_data_path = Path(tmpdir) / "9iwAGnskOkqzo_NZ" / "session_persistence.bin"
    session_data_path.parent.mkdir(parents=True)
    session_data_path.write_bytes(b"foo")

    if valid_session:
        call_result = {
            "result": {
                "user": {
                    "id": 1234,
                    "name": "You",
                },
                "encoded_session_b85": b"Ze@30VtI6Ba{",
            }
        }
    else:
        call_result = InvalidSessionError().as_json

    client.sio.call = AsyncMock(return_value=call_result)

    # Run
    await client.on_connect()

    # Assert
    client.sio.call.assert_awaited_once_with("restore_user_session", b"foo", namespace=None, timeout=30)

    if valid_session:
        assert client.connection_state == ConnectionState.Connected
        assert session_data_path.read_bytes() == b"new_bytes"
    else:
        assert client.connection_state == ConnectionState.ConnectedNotLogged
        assert not session_data_path.is_file()


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


async def test_connect_to_server(tmp_path):
    # Setup
    client = NetworkClient(tmp_path, {"server_address": "http://localhost:5000", "socketio_path": "/path"})

    async def connect(*args, **kwargs):
        client._waiting_for_on_connect.set_result(True)

    client.sio.connect = AsyncMock(side_effect=connect)
    client.sio.connected = False

    # Run
    await client.connect_to_server()

    # Assert
    assert client.connection_state == ConnectionState.Connecting
    client.sio.connect.assert_awaited_once_with(
        "http://localhost:5000", socketio_path="/path", transports=["websocket"], headers=connection_headers()
    )


async def test_connect_to_server_cancel(tmp_path):
    # Setup
    client = NetworkClient(tmp_path, {"server_address": "http://localhost:5000", "socketio_path": "/path"})

    client.sio.disconnect = AsyncMock()
    client._internal_connect_to_server = AsyncMock(side_effect=asyncio.CancelledError())

    # Run
    await client.connect_to_server()

    # Assert
    client.sio.disconnect.assert_awaited_once_with()


async def test_internal_connect_to_server_failure(tmp_path):
    # Setup
    client = NetworkClient(tmp_path, {"server_address": "http://localhost:5000", "socketio_path": "/path"})

    async def connect(*args, **kwargs):
        raise (aiohttp.client_exceptions.ContentTypeError(MagicMock(), (), message="thing"))

    client.sio.disconnect = AsyncMock()
    client.sio.connect = AsyncMock(side_effect=connect)
    client.sio.connected = False

    # Run
    with pytest.raises(UnableToConnect):
        await client._internal_connect_to_server()

    # Assert
    client.sio.disconnect.assert_awaited_once_with()


async def test_disconnect_from_server(client: NetworkClient):
    client.sio = AsyncMock()
    await client.disconnect_from_server()
    client.sio.disconnect.assert_awaited_once_with()


async def test_session_admin_global(client: NetworkClient):
    client.server_call = AsyncMock()

    game_session_meta = MagicMock()
    game_session_meta.id = 1234

    # Run
    result = await client.session_admin_global(game_session_meta, SessionAdminGlobalAction.CHANGE_WORLD, 5)

    # Assert
    assert result == client.server_call.return_value
    client.server_call.assert_awaited_once_with("multiplayer_admin_session", (1234, "change_world", 5))


@pytest.mark.parametrize("was_listening", [False, True])
@pytest.mark.parametrize("listen", [False, True])
async def test_listen_to_session(client: NetworkClient, listen, was_listening):
    client.server_call = AsyncMock()
    session_meta = MagicMock()
    session_meta.id = 1234
    if was_listening:
        client._sessions_interested_in.add(1234)

    # Run
    await client.listen_to_session(session_meta.id, listen)

    # Assert
    client.server_call.assert_awaited_once_with("multiplayer_listen_to_session", (1234, listen))
    if listen:
        assert client._sessions_interested_in == {1234}
    else:
        assert client._sessions_interested_in == set()


@pytest.mark.parametrize("was_listening", [False, True])
@pytest.mark.parametrize("listen", [False, True])
async def test_world_track_inventory(client: NetworkClient, listen, was_listening):
    uid = uuid.UUID("8b8b9269-1e54-42fe-9e5f-82875ef986e2")

    client.server_call = AsyncMock()
    client._tracking_worlds.add((uid, 9999))
    if was_listening:
        client._tracking_worlds.add((uid, 4567))

    # Run
    await client.world_track_inventory(uid, 4567, listen)

    # Assert
    client.server_call.assert_awaited_once_with("multiplayer_watch_inventory", (str(uid), 4567, listen, True))
    if listen:
        assert client._tracking_worlds == {(uid, 9999), (uid, 4567)}
    else:
        assert client._tracking_worlds == {(uid, 9999)}


async def test_emit_with_result_timeout(client: NetworkClient):
    # Setup
    client._connection_state = ConnectionState.Connected
    client.sio = AsyncMock()
    client.sio.call.side_effect = socketio.exceptions.TimeoutError()

    # Run
    with pytest.raises(RequestTimeoutError, match="Timeout after "):
        await client.server_call("test_event")


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


async def test_refresh_received_pickups(client: NetworkClient, corruption_game_description, mocker):
    db = corruption_game_description.resource_database

    data = {
        "world": "00000000-0000-1111-0000-000000000000",
        "game": RandovaniaGame.METROID_PRIME_CORRUPTION.value,
        "pickups": [
            {"provider_name": "Message A", "pickup": "VtI6Bb3p"},
            {"provider_name": "Message B", "pickup": "VtI6Bb3y"},
            {"provider_name": "Message C", "pickup": "VtI6Bb3*"},
        ],
    }

    pickups = [MagicMock(), MagicMock(), MagicMock()]
    mock_decode = mocker.patch("randovania.network_client.network_client._decode_pickup", side_effect=pickups)

    client.on_world_pickups_update = AsyncMock()

    # Run
    await client._on_world_pickups_update_raw(data)

    # Assert
    client.on_world_pickups_update.assert_awaited_once_with(
        MultiplayerWorldPickups(
            world_id=uuid.UUID("00000000-0000-1111-0000-000000000000"),
            game=RandovaniaGame.METROID_PRIME_CORRUPTION,
            pickups=(
                ("Message A", pickups[0]),
                ("Message B", pickups[1]),
                ("Message C", pickups[2]),
            ),
        )
    )
    mock_decode.assert_has_calls([call("VtI6Bb3p", db), call("VtI6Bb3y", db), call("VtI6Bb3*", db)])


def test_decode_pickup(
    client: NetworkClient, echoes_resource_database, generic_pickup_category, default_generator_params
):
    data = (
        "h^WxYK%Bzb%2NU&w=%giys9}cw>h&ixhA)=I<_*yXJu|>a%p3j6&;nimC2=yfhEzEw1EwU(UqOO$>p%O5KI8-+"
        "~(lQ#?s8v%E&;{=*rqdXJu|>a%p3j6&;nimC2=yfhEzEw1EwU(UqOO$>p%O5KI8-+~(lQ#?s8v%E&;{=*rpvSO"
    )
    expected_pickup = PickupEntry(
        name="The Name",
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        pickup_category=generic_pickup_category,
        broad_category=generic_pickup_category,
        progression=(),
        generator_params=default_generator_params,
    )

    # # Uncomment this to encode the data once again and get the new bytefield if it changed for some reason
    # from randovania.server.multiplayer.world_api import _base64_encode_pickup
    # new_data = _base64_encode_pickup(expected_pickup, echoes_resource_database)
    # assert new_data == data; assert False

    # Run
    pickup = _decode_pickup(data, echoes_resource_database)

    # Assert
    assert pickup == expected_pickup


async def test_on_disconnect(client: NetworkClient):
    client._restore_session_task = MagicMock()

    # Run
    await client.on_disconnect()

    # Assert
    client._restore_session_task.cancel.assert_called_once_with()
    assert client.connection_state == ConnectionState.Disconnected


async def test_create_new_session(client: NetworkClient, mocker: pytest_mock.MockerFixture):
    mock_session_from = mocker.patch("randovania.network_common.multiplayer_session.MultiplayerSessionEntry.from_json")
    client.server_call = AsyncMock()

    # Run
    result = await client.create_new_session("The Session")

    # Assert
    assert result is mock_session_from.return_value
    client.server_call.assert_awaited_once_with("multiplayer_create_session", "The Session")
    mock_session_from.assert_called_once_with(client.server_call.return_value)
    assert client._sessions_interested_in == {mock_session_from.return_value.id}


async def test_join_multiplayer_session(client: NetworkClient, mocker: pytest_mock.MockerFixture):
    session = MagicMock()
    mock_session_from = mocker.patch("randovania.network_common.multiplayer_session.MultiplayerSessionEntry.from_json")
    client.server_call = AsyncMock()

    # Run
    result = await client.join_multiplayer_session(session.id, "mahSecret")

    # Assert
    assert result is mock_session_from.return_value
    client.server_call.assert_awaited_once_with("multiplayer_join_session", (session.id, "mahSecret"))
    mock_session_from.assert_called_once_with(client.server_call.return_value)
    assert client._sessions_interested_in == {mock_session_from.return_value.id}


async def test_on_world_user_inventory_raw(client: NetworkClient):
    client.on_world_user_inventory = AsyncMock()
    uid = "00000000-0000-1111-0000-000000000000"
    item = ItemResourceInfo(0, "Super Key", "MyKey", 1)

    inventory = Inventory({item: InventoryItem(1, 4)})
    encoded = remote_inventory.inventory_to_encoded_remote(inventory)

    await client._on_world_user_inventory_raw(uid, 1234, encoded)
    client.on_world_user_inventory.assert_called_once_with(
        WorldUserInventory(
            world_id=uuid.UUID(uid),
            user_id=1234,
            inventory={"MyKey": 4},
        )
    )
