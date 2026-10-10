from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from randovania.game_connection.builder.yoku_connector_builder import YokuConnectorBuilder
from randovania.game_connection.connector.yoku_remote_connector import YokuRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_connection.executor.yoku_executor import YokuExecutor


async def test_general_class_content():
    builder = YokuConnectorBuilder("127.0.0.1")
    assert builder.configuration_params() == {"ip": "127.0.0.1"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.YOKU
    assert builder.pretty_text == "Yoku's Island Express: 127.0.0.1"


@pytest.mark.parametrize("depth", [0, 1])
async def test_create(depth: int):
    def __init__(self, ip):
        self.signals = ExecutorToConnectorSignals()
        self._ip = ip
        self.connect = AsyncMock(return_value=(None if depth == 0 else True))
        self.layout_uuid_str = "00000000-0000-1111-0000-000000000000"

    builder = YokuConnectorBuilder("127.0.0.1")

    with patch.object(YokuExecutor, "__init__", __init__):
        connector = await builder.build_connector()
        if depth == 0:
            assert isinstance(connector, YokuRemoteConnector)
            assert builder.get_status_message() == "Connected to 127.0.0.1"
        else:
            assert connector is None
            assert builder.get_status_message() == "Unable to connect to Yoku's Island Express"


@pytest.mark.usefixtures("is_dev_version")
def test_usable_only_where_the_game_is_visible(is_frozen: bool):
    assert ConnectorBuilderChoice.YOKU.is_usable() is not is_frozen
