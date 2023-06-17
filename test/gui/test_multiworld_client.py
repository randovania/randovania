import json
import uuid
from unittest.mock import MagicMock, AsyncMock, call

import pytest
from frozendict import frozendict
from pytest_mock import MockerFixture

from randovania.game_connection.game_connection import ConnectedGameState
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.multiworld_client import MultiworldClient, Data
from randovania.lib import json_lib
from randovania.network_common import error
from randovania.network_common.game_connection_status import GameConnectionStatus
from randovania.network_common.world_sync import ServerSyncRequest, ServerWorldSync, ServerSyncResponse, \
    ServerWorldResponse


@pytest.fixture()
def client(skip_qtbot, tmp_path):
    network_client = MagicMock()
    return MultiworldClient(network_client, MagicMock(), tmp_path.joinpath("persist"))


async def test_start(client):
    game_connection = client.game_connection

    # Run
    await client.start()

    # Assert
    game_connection.GameStateUpdated.connect.assert_called_once_with(client.on_game_state_updated)
    client.network_client.WorldPickupsUpdated.connect.assert_called_once_with(client.on_network_game_updated)


async def test_stop(client: MultiworldClient):
    sync_task = MagicMock()
    client._sync_task = sync_task

    # Run
    await client.stop()

    # Assert
    sync_task.cancel.assert_called_once_with()
    assert client._sync_task is None


@pytest.mark.parametrize("exists", [False, True])
async def test_on_game_state_updated(client: MultiworldClient, tmp_path, exists):
    the_id = uuid.UUID("00000000-0000-1111-0000-000000000000")
    data = Data(tmp_path.joinpath("data.json"))
    client._all_data = {the_id: data}
    data.collected_locations = {10, 15} if exists else {10}
    client.start_server_sync_task = MagicMock()

    remote_game = MagicMock()
    client._remote_games = {
        the_id: remote_game
    }

    connector = AsyncMock()
    state = MagicMock()
    state.id = the_id
    state.collected_indices = {PickupIndex(15)}
    state.source.set_remote_pickups = AsyncMock()
    client.game_connection.connected_states = {connector: state}

    # Run
    await client.on_game_state_updated(state)

    # Assert
    assert data.collected_locations == {10, 15}

    state.source.set_remote_pickups.assert_awaited_once_with(remote_game.pickups)
    client.start_server_sync_task.assert_called_once_with()


async def test_on_network_game_updated(client):
    client.start_server_sync_task = MagicMock()
    pickups = MagicMock()

    # Run
    await client.on_network_game_updated(pickups)

    # Assert
    assert client._remote_games == {
        pickups.world_id: pickups
    }
    client.start_server_sync_task.assert_called_once_with()


@pytest.mark.parametrize("has_last_status", [False, True])
@pytest.mark.parametrize("has_old_pending", [False, True])
def test_create_new_sync_request(client, tmp_path, has_old_pending, has_last_status):
    sync_requests = {}

    uid_1 = "11111111-0000-0000-0000-000000000000"
    uid_2 = "00000000-0000-1111-0000-000000000000"
    uid_3 = "000000000000-0000-0000-0000-11111111"

    client._persist_path.joinpath(f"{uid_1}.json").write_text(json.dumps({
        "collected_locations": [5],
        "uploaded_locations": [],
        "latest_message_displayed": 0,
    }))
    client.game_connection.connected_states = {
        MagicMock(): ConnectedGameState(
            id=uuid.UUID(uid_1),
            source=MagicMock(),
            status=GameConnectionStatus.InGame,
            current_inventory={},
            collected_indices=MagicMock(),
        )
    }
    sync_requests[uuid.UUID(uid_1)] = ServerWorldSync(
        status=GameConnectionStatus.InGame,
        collected_locations=(5,),
        inventory=frozendict({}),
        request_details=True,
    )

    if has_old_pending:
        data_path = tmp_path.joinpath("old-data.json")
        data_path.write_text(json.dumps({
            "collected_locations": [10, 15],
            "uploaded_locations": [15],
            "latest_message_displayed": 0,
        }))
        client._all_data[uuid.UUID(uid_2)] = Data(data_path)
        sync_requests[uuid.UUID(uid_2)] = ServerWorldSync(
            status=GameConnectionStatus.Disconnected,
            collected_locations=(10,),
            inventory=None,
            request_details=False,
        )

    if has_last_status:
        client._last_reported_status[uuid.UUID(uid_1)] = GameConnectionStatus.TitleScreen
        client._last_reported_status[uuid.UUID(uid_3)] = GameConnectionStatus.InGame
        sync_requests[uuid.UUID(uid_3)] = ServerWorldSync(
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


async def test_server_sync_identical(client):
    client._create_new_sync_request = MagicMock(return_value=ServerSyncRequest(worlds=frozendict({})))
    client.network_client.perform_world_sync = AsyncMock()

    # Run
    await client._server_sync()

    # Assert
    client.network_client.perform_world_sync.assert_not_awaited()


async def test_server_sync(client, mocker: MockerFixture):
    mock_sleep = mocker.patch("asyncio.sleep", new_callable=AsyncMock)

    uid_1 = uuid.UUID("11111111-0000-0000-0000-000000000000")
    uid_2 = uuid.UUID("00000000-0000-1111-0000-000000000000")
    uid_3 = uuid.UUID("000000000000-0000-0000-0000-11111111")

    request = ServerSyncRequest(worlds=frozendict({
        uid_1: ServerWorldSync(
            status=GameConnectionStatus.InGame,
            collected_locations=(5,),
            inventory=frozendict({}),
            request_details=True,
        ),
        uid_2: ServerWorldSync(
            status=GameConnectionStatus.TitleScreen,
            collected_locations=(),
            inventory=frozendict({}),
            request_details=False,
        ),
        uid_3: ServerWorldSync(
            status=GameConnectionStatus.Disconnected,
            collected_locations=(15, 20),
            inventory=frozendict({}),
            request_details=False,
        ),
    }))
    client._create_new_sync_request = MagicMock(side_effect=[
        request,
        request,  # the first perform_world_sync fails, so this is called again
        ServerSyncRequest(worlds=frozendict({})),  # Since the third world failed, the sync loop runs again.
    ])
    client.network_client.perform_world_sync = AsyncMock(side_effect=[
        error.RequestTimeout,
        ServerSyncResponse(
            worlds=frozendict({
                uid_1: ServerWorldResponse(
                    world_name="World 1",
                    session=MagicMock(),
                ),
            }),
            errors=frozendict({
                uid_3: error.InvalidAction("bad thing")
            }),
        ),
        ServerSyncResponse(frozendict({}), frozendict({})),
    ])

    # Run
    await client._server_sync()

    # Assert
    client.network_client.perform_world_sync.assert_has_awaits([
        call(request), call(request),
        call(ServerSyncRequest(worlds=frozendict({}))),
    ])
    mock_sleep.assert_has_awaits([
        call(5),  # first perform_world_sync call timed out
        call(5),  # the sync response had errors
    ])
    # TODO: test that the error handling

    assert json_lib.read_path(client._persist_path.joinpath(f"{uid_1}.json")) == {
        'collected_locations': [],
        'latest_message_displayed': 0,
        'uploaded_locations': [5]
    }

