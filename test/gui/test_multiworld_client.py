from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import pytest
from frozendict import frozendict

from randovania.game_connection.game_connection import ConnectedGameState
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.multiworld_client import MultiworldClient
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.interface_common.world_database import WorldData, WorldDatabase, WorldServerData
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.multiplayer_session import MultiplayerUser, MultiplayerWorld
from randovania.network_common.world_sync import (
    ServerSyncRequest,
    ServerSyncResponse,
    ServerWorldResponse,
    ServerWorldSync,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.fixture()
def client(skip_qtbot, tmp_path):
    network_client = MagicMock()
    return MultiworldClient(network_client, MagicMock(), WorldDatabase(tmp_path.joinpath("persist")))


async def test_start(client):
    game_connection = client.game_connection
    client.start_server_sync_task = MagicMock()

    # Run
    await client.start()

    # Assert
    game_connection.GameStateUpdated.connect.assert_called_once_with(client.on_game_state_updated)
    client.network_client.WorldPickupsUpdated.connect.assert_called_once_with(client.on_network_game_updated)
    client.start_server_sync_task.assert_called_once_with()


async def test_stop(client: MultiworldClient):
    sync_task = MagicMock()
    client._sync_task = sync_task

    # Run
    await client.stop()

    # Assert
    sync_task.cancel.assert_called_once_with()
    assert client._sync_task is None


async def test_start_server_sync_task(client):
    client._server_sync = AsyncMock()

    # Run
    client.start_server_sync_task()
    await client._sync_task

    # Assert
    client._server_sync.assert_awaited_once_with()
    assert client._sync_task.done()


@pytest.mark.parametrize("exists", [False, True, "invalid"])
async def test_on_game_state_updated(client: MultiworldClient, tmp_path, exists):
    the_id = INVALID_UUID if exists == "invalid" else uuid.UUID("00000000-0000-0000-1111-000000000000")
    data = WorldData(collected_locations=(10, 15) if exists else (10,))
    if exists == "invalid":
        client._all_data = {}
    else:
        client.database._all_data[the_id] = data
    client.start_server_sync_task = MagicMock()

    remote_game = MagicMock()
    client._remote_games = {the_id: remote_game}

    connector = AsyncMock()
    state = MagicMock()
    state.id = the_id
    state.collected_indices = {PickupIndex(15)}
    state.source.set_remote_pickups = AsyncMock()
    client.game_connection.connected_states = {connector: state}

    # Run
    await client.on_game_state_updated(state)

    # Assert
    if exists == "invalid":
        state.source.set_remote_pickups.assert_not_awaited()
        client.start_server_sync_task.assert_not_called()
    else:
        assert client.database.get_data_for(the_id).collected_locations == (10, 15)
        state.source.set_remote_pickups.assert_awaited_once_with(remote_game.pickups)
        client.start_server_sync_task.assert_called_once_with()


async def test_on_network_game_updated(client):
    client.start_server_sync_task = MagicMock()
    pickups = MagicMock()

    # Run
    await client.on_network_game_updated(pickups)

    # Assert
    assert client._remote_games == {pickups.world_id: pickups}
    client.start_server_sync_task.assert_called_once_with()


@pytest.mark.parametrize("has_last_status", [False, True])
@pytest.mark.parametrize("has_old_pending", [False, True])
def test_create_new_sync_request(client, has_old_pending, has_last_status):
    sync_requests = {}

    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")
    uid_2 = uuid.UUID("00000000-0000-0000-1111-000000000000")
    uid_3 = uuid.UUID("000000000000-0000-0000-0000-11111111")
    uid_4 = uuid.UUID("22222222-0000-0000-0000-000000000000")

    client._world_sync_errors[uid_1] = error.ServerError()
    client._world_sync_errors[uid_4] = error.WorldDoesNotExistError()
    client.database._all_data[uid_1] = WorldData(
        collected_locations=(5,),
    )
    client.database._all_data[uid_4] = WorldData(
        collected_locations=(55,),
    )
    client.game_connection.connected_states = {
        MagicMock(): ConnectedGameState(
            id=uid_1,
            source=MagicMock(),
            status=GameConnectionStatus.InGame,
            current_inventory=Inventory.empty(),
            collected_indices=MagicMock(),
        ),
        MagicMock(): ConnectedGameState(
            id=INVALID_UUID,
            source=MagicMock(),
            status=GameConnectionStatus.InGame,
            current_inventory=Inventory.empty(),
            collected_indices=MagicMock(),
        ),
        MagicMock(): ConnectedGameState(
            id=uid_4,
            source=MagicMock(),
            status=GameConnectionStatus.InGame,
            current_inventory=Inventory.empty(),
            collected_indices=MagicMock(),
        ),
    }
    sync_requests[uid_1] = ServerWorldSync(
        status=GameConnectionStatus.InGame,
        collected_locations=(5,),
        inventory=b"\x00",
        request_details=True,
    )

    if has_old_pending:
        client.database._all_data[uid_2] = WorldData(
            collected_locations=(10, 15),
            uploaded_locations=(15,),
        )
        sync_requests[uid_2] = ServerWorldSync(
            status=GameConnectionStatus.Disconnected,
            collected_locations=(10,),
            inventory=None,
            request_details=False,
        )

    if has_last_status:
        client._last_reported_status[uid_1] = GameConnectionStatus.TitleScreen
        client._last_reported_status[uid_3] = GameConnectionStatus.InGame
        sync_requests[uid_3] = ServerWorldSync(
            status=GameConnectionStatus.Disconnected,
            collected_locations=(),
            inventory=None,
            request_details=False,
        )

    # Run
    result = client._create_new_sync_request()

    # Assert
    assert result == ServerSyncRequest(
        worlds=frozendict(sync_requests),
    )


async def test_server_sync_identical(client, mocker: MockerFixture):
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    client._create_new_sync_request = MagicMock(return_value=ServerSyncRequest(worlds=frozendict({})))
    client.network_client.perform_world_sync = AsyncMock()

    # Run
    await client._server_sync()

    # Assert
    client.network_client.perform_world_sync.assert_not_awaited()
    mock_sleep.assert_called_once_with(1)


async def test_server_sync(client, mocker: MockerFixture):
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")
    uid_2 = uuid.UUID("00000000-0000-1111-0000-000000000000")
    uid_3 = uuid.UUID("000000000000-0000-0000-0000-11111111")

    request = ServerSyncRequest(
        worlds=frozendict(
            {
                uid_1: ServerWorldSync(
                    status=GameConnectionStatus.InGame,
                    collected_locations=(5,),
                    inventory=b"foo",
                    request_details=True,
                ),
                uid_2: ServerWorldSync(
                    status=GameConnectionStatus.TitleScreen,
                    collected_locations=(),
                    inventory=b"bar",
                    request_details=False,
                ),
                uid_3: ServerWorldSync(
                    status=GameConnectionStatus.Disconnected,
                    collected_locations=(15, 20),
                    inventory=None,
                    request_details=False,
                ),
            }
        )
    )
    client._create_new_sync_request = MagicMock(
        side_effect=[
            request,
            request,  # the first perform_world_sync fails, so this is called again
            ServerSyncRequest(worlds=frozendict({})),  # Since the third world failed, the sync loop runs again.
            ServerSyncRequest(worlds=frozendict({})),  # And a last time, to make sure there were no new requests
        ]
    )
    client.network_client.perform_world_sync = AsyncMock(
        side_effect=[
            error.RequestTimeoutError,
            ServerSyncResponse(
                worlds=frozendict(
                    {
                        uid_1: ServerWorldResponse(
                            world_name="World 1",
                            session_id=567,
                            session_name="The Session",
                        ),
                    }
                ),
                errors=frozendict({uid_3: error.WorldDoesNotExistError()}),
            ),
            ServerSyncResponse(frozendict({}), frozendict({})),
        ]
    )

    # Run
    await client._server_sync()

    # Assert
    client.network_client.perform_world_sync.assert_has_awaits(
        [
            call(request),
            call(request),
            call(ServerSyncRequest(worlds=frozendict({}))),
        ]
    )
    mock_sleep.assert_has_awaits(
        [
            # First request
            call(1),
            call(15),  # perform_world_sync call timed out
            # Second request
            call(1),
            call(4),  # the sync response had errors
            # Third request
            call(1),
            call(4),  # the sync response was successful
            # Fourth request
            call(1),  # identical to last, ends
        ]
    )
    # TODO: test that the error handling

    assert client.database.get_data_for(uid_1) == WorldData(
        uploaded_locations=(5,),
        server_data=WorldServerData(
            world_name="World 1",
            session_id=567,
            session_name="The Session",
        ),
    )
    assert client._world_sync_errors == {
        uid_3: error.WorldDoesNotExistError(),
    }


async def test_on_session_meta_update_not_logged_in(client: MultiworldClient):
    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")
    uid_2 = uuid.UUID("11111111-0000-0000-0000-111111111111")

    entry = MagicMock()
    entry.worlds = [MultiplayerWorld(id=uid_1, name="Names", preset_raw="{}")]
    client.network_client.current_user = None
    client._world_sync_errors[uid_1] = error.WorldDoesNotExistError()
    client._world_sync_errors[uid_2] = error.WorldNotAssociatedError()

    # Run
    await client.on_session_meta_update(entry)

    # Assert
    assert client._world_sync_errors == {uid_2: error.WorldNotAssociatedError()}


async def test_on_session_meta_update_not_in_session(client: MultiworldClient):
    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")

    entry = MagicMock()
    entry.worlds = [MultiplayerWorld(id=uid_1, name="Names", preset_raw="{}")]
    entry.users = {}
    client._world_sync_errors[uid_1] = error.WorldNotAssociatedError()

    # Run
    await client.on_session_meta_update(entry)

    # Assert
    assert client._world_sync_errors == {
        uid_1: error.WorldNotAssociatedError(),
    }


async def test_on_session_meta_update_not_own_world(client: MultiworldClient):
    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")
    uid_2 = uuid.UUID("11111111-0000-0000-0000-111111111111")

    entry = MagicMock()
    entry.users = {
        client.network_client.current_user.id: MultiplayerUser(10, "You", False, False, {uid_2: MagicMock()})
    }
    client._world_sync_errors[uid_1] = error.WorldNotAssociatedError()

    # Run
    await client.on_session_meta_update(entry)

    # Assert
    assert client._world_sync_errors == {uid_1: error.WorldNotAssociatedError()}
