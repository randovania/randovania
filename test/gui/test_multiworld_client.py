import json
from pathlib import Path

import pytest
from mock import MagicMock, AsyncMock, call

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.gui.multiworld_client import MultiworldClient, Data


@pytest.fixture(name="client")
def _client(skip_qtbot):
    network_client = MagicMock()
    game_connection = MagicMock()
    game_connection.backend.lock_identifier = None
    return MultiworldClient(network_client, game_connection)


@pytest.mark.asyncio
async def test_start(client, tmpdir):
    game_connection = client.game_connection

    client.network_client.game_session_request_pickups = AsyncMock(return_value=[])
    client.network_client.session_self_update = AsyncMock()
    client.refresh_received_pickups = AsyncMock()
    client._received_messages = ["Foo"]
    client._received_pickups = ["Pickup"]

    # Run
    await client.start(Path(tmpdir).joinpath("missing_file.json"))

    # Assert
    client.refresh_received_pickups.assert_awaited_once_with()
    game_connection.set_location_collected_listener.assert_called_once_with(client.on_location_collected)
    client.network_client.GameUpdateNotification.connect.assert_called_once_with(client.on_network_game_updated)
    game_connection.set_permanent_pickups.assert_called_once_with(["Pickup"])


@pytest.mark.asyncio
async def test_stop(client):
    # Run
    await client.stop()

    # Assert
    client.game_connection.set_location_collected_listener.assert_called_once_with(None)
    client.network_client.GameUpdateNotification.disconnect.assert_called_once_with(client.on_network_game_updated)
    client.game_connection.set_permanent_pickups.assert_called_once_with([])


@pytest.mark.parametrize("exists", [False, True])
@pytest.mark.asyncio
async def test_on_location_collected(client, tmpdir, exists):
    client._data = Data(Path(tmpdir).joinpath("data.json"))
    client._data.collected_locations = {10, 15} if exists else {10}
    client.start_notify_collect_locations_task = MagicMock()

    # Run
    await client.on_location_collected(15)

    # Assert
    assert client._data.collected_locations == {10, 15}

    if exists:
        client.start_notify_collect_locations_task.assert_not_called()
    else:
        client.start_notify_collect_locations_task.assert_called_once_with()


@pytest.mark.asyncio
async def test_refresh_received_pickups(client):
    results = [
        ("Message A", b"bytesA"),
        ("Message B", b"bytesB"),
        ("Message C", b"bytesC"),
    ]

    client.network_client.game_session_request_pickups = AsyncMock(return_value=results)

    pickups = [MagicMock(), MagicMock(), MagicMock()]
    client._decode_pickup = MagicMock(side_effect=pickups)

    # Run
    await client.refresh_received_pickups()

    # Assert
    assert client._received_pickups == list(zip(["Message A", "Message B", "Message C"], pickups))
    client._decode_pickup.assert_has_calls([call(b"bytesA"), call(b"bytesB"), call(b"bytesC")])


@pytest.mark.asyncio
async def test_on_game_updated(client, tmpdir):
    client.refresh_received_pickups = AsyncMock()
    client._received_pickups = MagicMock()

    client._data = Data(Path(tmpdir).joinpath("data.json"))

    # Run
    await client.on_network_game_updated()

    # Assert
    client.game_connection.set_permanent_pickups.assert_called_once_with(client._received_pickups)


def test_decode_pickup(client, echoes_resource_database):
    data = b"\x80*42\x90'0\xb6\xb2\x80d \x00"
    expected_pickup = PickupEntry(
        name="The Name",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        broad_category=ItemCategory.MOVEMENT,
        resources=(
            ConditionalResources(None, None, ()),
        ),
    )

    # from randovania.bitpacking import bitpacking
    # from randovania.network_common.pickup_serializer import BitPackPickupEntry
    # new_data = bitpacking.pack_value(BitPackPickupEntry(expected_pickup, echoes_resource_database))
    # assert new_data == data

    # Run
    pickup = client._decode_pickup(data)

    # Assert
    assert pickup == expected_pickup


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
    network_client.game_session_request_pickups = AsyncMock(return_value=[])
    network_client.session_self_update = AsyncMock()
    game_connection = MagicMock()
    game_connection.backend.lock_identifier = str(tmpdir.join("my-lock"))

    # Run
    client = MultiworldClient(network_client, game_connection)
    assert tmpdir.join("my-lock.pid").exists()

    await client.start(Path(tmpdir).joinpath("data.json"))
    await client.stop()
    assert not tmpdir.join("my-lock.pid").exists()
