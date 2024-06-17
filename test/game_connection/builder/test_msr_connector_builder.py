from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from randovania.game_connection.builder.msr_connector_builder import MSRConnectorBuilder
from randovania.game_connection.connector.msr_remote_connector import MSRRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_connection.executor.msr_executor import MSRExecutor


async def test_general_class_content():
    builder = MSRConnectorBuilder("localhost")
    assert builder.configuration_params() == {"ip": "localhost"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.MSR
    assert builder.pretty_text == "Samus Returns: localhost"


@pytest.mark.parametrize("depth", [0, 1])
async def test_create(depth: int):
    def __init__(self, ip):
        self.signals = ExecutorToConnectorSignals()
        self._ip = ip
        self.connect = AsyncMock(return_value=(None if depth == 0 else True))
        self.layout_uuid_str = "00000000-0000-1111-0000-000000000000"

    builder = MSRConnectorBuilder("localhost")

    with patch.object(MSRExecutor, "__init__", __init__):
        connector = await builder.build_connector()
        if depth == 0:
            assert isinstance(connector, MSRRemoteConnector)
            assert builder.get_status_message() == "Connected to localhost"
        else:
            assert connector is None
            assert builder.get_status_message() == "Unable to connect to Samus Returns"
