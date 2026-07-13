from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.builder.abandoned_world_connector_builder import AbandonedWorldConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_client.network_client import ConnectionState
from randovania.network_common import error


def make_builder() -> AbandonedWorldConnectorBuilder:
    return AbandonedWorldConnectorBuilder.create(
        RandovaniaGame.BLANK,
        uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )


async def test_build_connector_no_network_client():
    builder = make_builder()
    assert builder.network_client is None

    assert await builder.build_connector() is None
    message = builder.get_status_message()
    assert message
    assert "connection to the server" in message.lower()


async def test_build_connector_not_connected():
    builder = make_builder()
    builder.network_client = MagicMock()
    builder.network_client.connection_state = ConnectionState.Disconnected

    assert await builder.build_connector() is None


async def test_build_connector_success(default_preset, mocker):
    builder = make_builder()
    builder.network_client = MagicMock()
    builder.network_client.connection_state = ConnectionState.Connected

    preset_raw = json.dumps(VersionedPreset.with_preset(default_preset).as_json)
    builder.network_client.get_abandoned_world_data = AsyncMock(
        return_value={
            "order": 2,
            "preset_raw": preset_raw,
            "game_modifications": {"the": "modifications"},
            "collected_locations": [3, 5],
        }
    )
    mock_connector = mocker.patch(
        "randovania.game_connection.builder.abandoned_world_connector_builder.AbandonedWorldRemoteConnector",
        autospec=True,
    )

    result = await builder.build_connector()

    assert result is mock_connector.return_value
    builder.network_client.get_abandoned_world_data.assert_awaited_once_with(builder.layout_uuid)
    args = mock_connector.call_args.args
    assert args[0] == builder.layout_uuid
    assert args[1].as_json == VersionedPreset.with_preset(default_preset).as_json
    assert args[2:] == (2, {"the": "modifications"}, [3, 5])
    assert builder.get_status_message() is None


async def test_build_connector_error_backs_off(mocker):
    builder = make_builder()
    builder.network_client = MagicMock()
    builder.network_client.connection_state = ConnectionState.Connected
    builder.network_client.get_abandoned_world_data = AsyncMock(side_effect=error.NotAuthorizedForActionError())

    assert await builder.build_connector() is None
    assert builder.get_status_message() is not None
    assert not builder.no_longer_usable

    # The next attempt within the retry interval doesn't contact the server again.
    assert await builder.build_connector() is None
    builder.network_client.get_abandoned_world_data.assert_awaited_once()


async def test_build_connector_world_not_claimed():
    builder = make_builder()
    builder.network_client = MagicMock()
    builder.network_client.connection_state = ConnectionState.Connected
    builder.network_client.get_abandoned_world_data = AsyncMock(side_effect=error.WorldNotAssociatedError())

    assert await builder.build_connector() is None
    assert builder.no_longer_usable


def test_configuration_params_round_trip():
    builder = make_builder()
    params = builder.configuration_params()

    restored = AbandonedWorldConnectorBuilder(**params)
    assert restored.target_game == builder.target_game
    assert restored.layout_uuid == builder.layout_uuid
    assert restored.connector_builder_choice == ConnectorBuilderChoice.ABANDONED
