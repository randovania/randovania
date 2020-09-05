import pytest
from mock import MagicMock, AsyncMock, call

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.gui.multiworld_client import MultiworldClient


@pytest.mark.asyncio
async def test_start(skip_qtbot):
    network_client = MagicMock()
    network_client.game_session_request_pickups = AsyncMock(return_value=[])

    game_connection = MagicMock()
    client = MultiworldClient(network_client, game_connection)
    client.refresh_received_pickups = AsyncMock()
    client._received_messages = ["Foo"]
    client._received_pickups = ["Pickup"]

    # Run
    await client.start()

    # Assert
    client.refresh_received_pickups.assert_awaited_once_with()
    game_connection.LocationCollected.connect.assert_called_once_with(client.on_location_collected)
    network_client.GameUpdateNotification.connect.assert_called_once_with(client.on_game_updated)
    assert client.latest_message_displayed == 1
    game_connection.set_permanent_pickups.assert_called_once_with(["Pickup"])


@pytest.mark.asyncio
async def test_stop(skip_qtbot):
    network_client = MagicMock()
    game_connection = MagicMock()
    client = MultiworldClient(network_client, game_connection)

    # Run
    await client.stop()

    # Assert
    game_connection.LocationCollected.disconnect.assert_called_once_with(client.on_location_collected)
    network_client.GameUpdateNotification.disconnect.assert_called_once_with(client.on_game_updated)
    game_connection.set_permanent_pickups.assert_called_once_with([])


@pytest.mark.parametrize("is_local", [False, True])
@pytest.mark.asyncio
async def test_on_location_collected(skip_qtbot, is_local):
    if is_local:
        pickup_bytes = b"asdf"
    else:
        pickup_bytes = None

    network_client = MagicMock()
    network_client.game_session_collect_pickup = AsyncMock(return_value=pickup_bytes)
    game_connection = MagicMock()

    client = MultiworldClient(network_client, game_connection)
    client._decode_pickup = MagicMock()

    # Run
    await client.on_location_collected(15)

    # Assert
    network_client.game_session_collect_pickup.assert_awaited_once_with(PickupIndex(15))
    if is_local:
        client._decode_pickup.assert_called_once_with(pickup_bytes)
        game_connection.send_pickup.assert_called_once_with(client._decode_pickup.return_value)
    else:
        client._decode_pickup.assert_not_called()
        game_connection.send_pickup.assert_not_called()


@pytest.mark.asyncio
async def test_refresh_received_pickups(skip_qtbot):
    results = [
        ("Message A", b"bytesA"),
        ("Message B", b"bytesB"),
        ("Message C", b"bytesC"),
    ]

    network_client = MagicMock()
    network_client.game_session_request_pickups = AsyncMock(return_value=results)
    game_connection = MagicMock()

    pickups = [MagicMock(), MagicMock(), MagicMock()]
    client = MultiworldClient(network_client, game_connection)
    client._decode_pickup = MagicMock(side_effect=pickups)

    # Run
    await client.refresh_received_pickups()

    # Assert
    assert client._received_messages == ["Message A", "Message B", "Message C"]
    assert client._received_pickups == pickups
    client._decode_pickup.assert_has_calls([call(b"bytesA"), call(b"bytesB"), call(b"bytesC")])


@pytest.mark.asyncio
async def test_on_game_updated(skip_qtbot):
    network_client = MagicMock()

    game_connection = MagicMock()
    game_connection.display_message = AsyncMock()

    client = MultiworldClient(network_client, game_connection)
    client.refresh_received_pickups = AsyncMock()
    client._received_messages = ["Message A", "Message B", "Message C"]
    client._received_pickups = [MagicMock(), MagicMock(), MagicMock()]
    client.latest_message_displayed = 1

    # Run
    await client.on_game_updated()

    # Assert
    game_connection.display_message.assert_has_awaits([call("Message B"), call("Message C")])
    game_connection.set_permanent_pickups.assert_called_once_with(client._received_pickups)
    assert client.latest_message_displayed == 3


def test_decode_pickup(skip_qtbot):
    data = b'\x00\xd0\x00'
    client = MultiworldClient(MagicMock(), MagicMock())
    expected_pickup = PickupEntry(
        name="",
        model_index=0,
        item_category=ItemCategory.MOVEMENT,
        resources=(
            ConditionalResources(None, None, ()),
        ),
    )

    # Run
    pickup = client._decode_pickup(data)

    # Assert
    assert pickup == expected_pickup
