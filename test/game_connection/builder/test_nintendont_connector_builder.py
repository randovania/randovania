from __future__ import annotations

from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor


def test_create():
    builder = NintendontConnectorBuilder("102.168.1.1")
    assert builder.configuration_params() == {"ip": "102.168.1.1"}
    assert builder.connector_builder_choice == ConnectorBuilderChoice.NINTENDONT
    assert builder.pretty_text == "Nintendont: 102.168.1.1"

    executor = builder.create_executor()
    assert isinstance(executor, NintendontExecutor)
    assert executor.ip == "102.168.1.1"
