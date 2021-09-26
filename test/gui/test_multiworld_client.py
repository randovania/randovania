import json
from pathlib import Path

import pytest
from mock import MagicMock, AsyncMock, call

from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.gui import multiworld_client
from randovania.gui.multiworld_client import MultiworldClient, Data


@pytest.fixture(name="client")
def _client(skip_qtbot):
    network_client = MagicMock()
    game_connection = MagicMock(spec=GameConnection)
    game_connection.lock_identifier = None
    return MultiworldClient(network_client, game_connection)


@pytest.mark.asyncio
async def test_start(client, tmpdir):
    game_connection = client.game_connection

    client.network_client.game_session_request_pickups = AsyncMock(return_value=[])
    client.network_client.game_session_request_update = AsyncMock()
    client.network_client.session_self_update = AsyncMock()

    # Run
    await client.start(Path(tmpdir).joinpath("missing_file.json"))

    # Assert
    game_connection.set_location_collected_listener.assert_called_once_with(client.on_location_collected)
    client.network_client.GameSessionPickupsUpdated.connect.assert_called_once_with(client.on_network_game_updated)


@pytest.mark.asyncio
async def test_stop(client: MultiworldClient):
    # Run
    await client.stop()

    # Assert
    client.game_connection.set_location_collected_listener.assert_called_once_with(None)
    client.network_client.GameSessionPickupsUpdated.disconnect.assert_called_once_with(client.on_network_game_updated)
    client.game_connection.set_expected_game.assert_called_once_with(None)
    client.game_connection.set_permanent_pickups.assert_called_once_with(())


@pytest.mark.parametrize("wrong_game", [False, True])
@pytest.mark.parametrize("exists", [False, True])
@pytest.mark.asyncio
async def test_on_location_collected(client: MultiworldClient, tmpdir, exists, wrong_game):
    client._data = Data(Path(tmpdir).joinpath("data.json"))
    client._data.collected_locations = {10, 15} if exists else {10}
    client.start_notify_collect_locations_task = MagicMock()

    if wrong_game and not exists:
        expected_locations = {10}
    else:
        expected_locations = {10, 15}

    if not wrong_game:
        client._expected_game = RandovaniaGame.METROID_PRIME_ECHOES

    # Run
    await client.on_location_collected(RandovaniaGame.METROID_PRIME_ECHOES, PickupIndex(15))

    # Assert
    assert client._data.collected_locations == expected_locations

    if exists or wrong_game:
        client.start_notify_collect_locations_task.assert_not_called()
    else:
        client.start_notify_collect_locations_task.assert_called_once_with()


@pytest.mark.asyncio
async def test_on_game_updated(client, tmpdir):
    client._data = Data(Path(tmpdir).joinpath("data.json"))
    pickups = MagicMock()

    # Run
    await client.on_network_game_updated(pickups)

    # Assert
    client.game_connection.set_expected_game.assert_called_once_with(pickups.game)
    client.game_connection.set_permanent_pickups.assert_called_once_with(pickups.pickups)


@pytest.mark.asyncio
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
    client._data = Data(data_path)

    # Run
    await client._notify_collect_locations()

    # Assert
    network_client.game_session_collect_locations.assert_has_awaits([call((10,)), call((10,))])
    assert set(json.loads(data_path.read_text())["uploaded_locations"]) == {10, 15}


@pytest.mark.asyncio
async def test_lock_file_on_init(skip_qtbot, tmpdir):
    # Setup
    network_client = MagicMock()
    network_client.game_session_request_update = AsyncMock()
    network_client.session_self_update = AsyncMock()
    game_connection = MagicMock(spec=GameConnection)
    game_connection.lock_identifier = str(tmpdir.join("my-lock"))

    # Run
    client = MultiworldClient(network_client, game_connection)
    assert tmpdir.join("my-lock.pid").exists()

    await client.start(Path(tmpdir).joinpath("data.json"))
    await client.stop()
    assert not tmpdir.join("my-lock.pid").exists()
