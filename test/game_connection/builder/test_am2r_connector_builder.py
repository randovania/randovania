from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from randovania.game_connection.builder.am2r_connector_builder import AM2RConnectorBuilder
from randovania.game_connection.connector.am2r_remote_connector import AM2RRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.am2r_executor import AM2RExecutor
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals


async def test_general_class_content():
    builder = AM2RConnectorBuilder("localhost")
    assert builder.configuration_params() == {"ip": "localhost"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.AM2R
    assert builder.pretty_text == "AM2R: localhost"


@pytest.mark.parametrize("depth", [0, 1])
async def test_create(depth: int):
    def __init__(self, ip):
        self.signals = ExecutorToConnectorSignals()
        self._ip = ip
        self.connect = AsyncMock(return_value=(None if depth == 0 else True))
        self.layout_uuid_str = "00000000-0000-1111-0000-000000000000"

    builder = AM2RConnectorBuilder("localhost")

    with patch.object(AM2RExecutor, "__init__", __init__):
        connector = await builder.build_connector()
        if depth == 0:
            assert isinstance(connector, AM2RRemoteConnector)
            assert builder.get_status_message() == "Connected to localhost"
        else:
            assert connector is None
            assert builder.get_status_message() == "Unable to connect to AM2R"
