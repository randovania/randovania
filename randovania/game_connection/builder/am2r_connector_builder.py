from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.builder.socket_connector_builder import SocketConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.am2r_executor import AM2RExecutor


class AM2RConnectorBuilder(SocketConnectorBuilder):
    _game_display_name: ClassVar[str] = "AM2R"

    @property
    @override
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.AM2R

    @override
    def create_executor(self) -> AM2RExecutor:
        from randovania.game_connection.executor.am2r_executor import AM2RExecutor

        return AM2RExecutor(self.ip)

    @override
    def create_connector(self, executor: AM2RExecutor) -> RemoteConnector:
        from randovania.game_connection.connector.am2r_remote_connector import AM2RRemoteConnector

        return AM2RRemoteConnector(executor)
