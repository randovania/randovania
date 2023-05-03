import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, call

import pytest

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.multiworld_client import MultiworldClient, Data


@pytest.fixture(name="client")
def _client(skip_qtbot):
    network_client = MagicMock()
    game_connection = MagicMock(spec=GameConnection)
    game_connection.lock_identifier = None
    return MultiworldClient(network_client, game_connection)


async def test_start(client, tmpdir):
    game_connection = client.game_connection

    client.network_client.game_session_request_pickups = AsyncMock(return_value=[])
    client.network_client.game_session_request_update = AsyncMock()
    client.network_client.session_self_update = AsyncMock()

    # Run
    await client.start(Path(tmpdir).joinpath("state"))

    # Assert
    game_connection.GameStateUpdated.connect.assert_called_once_with(client.on_game_state_updated)
    client.network_client.GameSessionPickupsUpdated.connect.assert_called_once_with(client.on_network_game_updated)


async def test_stop(client: MultiworldClient):
    # Run
    await client.stop()

    # Assert
    client.game_connection.GameStateUpdated.disconnect.assert_called_once_with(client.on_game_state_updated)
    client.network_client.GameSessionPickupsUpdated.disconnect.assert_called_once_with(client.on_network_game_updated)
    assert client._remote_games == {}
    assert client._all_data is None


@pytest.mark.parametrize("exists", [False, True])
async def test_on_new_state(client: MultiworldClient, tmpdir, exists):
    the_id = uuid.UUID("00000000-0000-1111-0000-000000000000")
    data = Data(Path(tmpdir).joinpath("data.json"))
    client._all_data = {the_id: data}
    data.collected_locations = {10, 15} if exists else {10}
    client.start_notify_collect_locations_task = MagicMock()

    remote_game = MagicMock()
    client._remote_games = {
        the_id: remote_game
    }

    connector = AsyncMock()
    state = MagicMock()
    state.id = the_id
    state.collected_indices = {PickupIndex(15)}
    client.game_connection.connected_states = {connector: state}

    # Run
    await client._on_new_state()

    # Assert
    assert data.collected_locations == {10, 15}

    connector.set_remote_pickups.assert_awaited_once_with(remote_game.pickups)

    if exists:
        client.start_notify_collect_locations_task.assert_not_called()
    else:
        client.start_notify_collect_locations_task.assert_called_once_with()


async def test_on_game_state_updated(client):
    client._on_new_state = AsyncMock()
    await client.on_game_state_updated(MagicMock())
    client._on_new_state.assert_awaited_once_with()


async def test_on_network_game_updated(client, tmpdir):
    client._on_new_state = AsyncMock()
    pickups = MagicMock()

    # Run
    await client.on_network_game_updated(pickups)

    # Assert
    client._on_new_state.assert_awaited_once_with()
    assert client._remote_games == {
        pickups.id: pickups
    }


async def test_notify_collect_locations(client, tmpdir):
    data_path = Path(tmpdir).joinpath("data.json")
    network_client = client.network_client
    network_client.game_session_collect_locations = AsyncMock(side_effect=[
        RuntimeError("connection issue!"),
        None,
    ])

    data_path.write_text(json.dumps({
        "collected_locations": [10, 15],
        "uploaded_locations": [15],
        "latest_message_displayed": 0,
    }))
    client._all_data = {
        uuid.UUID("00000000-0000-1111-0000-000000000000"): Data(data_path)
    }

    # Run
    await client._notify_collect_locations()

    # Assert
    network_client.game_session_collect_locations.assert_has_awaits([call((10,)), call((10,))])
    assert set(json.loads(data_path.read_text())["uploaded_locations"]) == {10, 15}
