from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from randovania.game_connection.builder.dread_connector_builder import DreadConnectorBuilder
from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.dread_executor import DreadExecutor
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals


async def test_general_class_content():
    builder = DreadConnectorBuilder("localhost")
    assert builder.configuration_params() == {"ip": "localhost"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.DREAD
    assert builder.pretty_text == "Dread: localhost"


@pytest.mark.parametrize("depth", [0, 1])
async def test_create(depth: int):
    def __init__(self, ip):
        self.signals = ExecutorToConnectorSignals()
        self._ip = ip
        self.connect = AsyncMock(return_value=(None if depth == 0 else True))
        self.layout_uuid_str = "00000000-0000-1111-0000-000000000000"

    builder = DreadConnectorBuilder("localhost")

    with patch.object(DreadExecutor, "__init__", __init__):
        connector = await builder.build_connector()
        if depth == 0:
            assert isinstance(connector, DreadRemoteConnector)
            assert builder.get_status_message() == "Connected to localhost"
        else:
            assert connector is None
            assert builder.get_status_message() == "Unable to connect to Dread"
