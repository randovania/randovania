from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from randovania.game_connection.builder.cs_connector_builder import CSConnectorBuilder
from randovania.game_connection.connector.cs_remote_connector import CSRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.cs_executor import CSExecutor


async def test_general_class_content():
    builder = CSConnectorBuilder("localhost")
    assert builder.configuration_params() == {"ip": "localhost"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.CS
    assert builder.pretty_text == "Cave Story: localhost"


@pytest.mark.parametrize("depth", [0, 1])
async def test_create(depth: int):
    def __init__(self, ip):
        self.server_info = MagicMock()
        self._ip = ip
        self.connect = AsyncMock(return_value=(None if depth == 0 else True))

    builder = CSConnectorBuilder("localhost")

    with patch.object(CSExecutor, "__init__", __init__):
        connector = await builder.build_connector()
        if depth == 0:
            assert isinstance(connector, CSRemoteConnector)
            assert builder.get_status_message() == "Connected to localhost"
        else:
            assert connector is None
            assert builder.get_status_message() == "Unable to connect to Cave Story"
