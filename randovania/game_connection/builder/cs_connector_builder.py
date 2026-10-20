from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.builder.socket_connector_builder import SocketConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.cs_executor import CSExecutor


class CSConnectorBuilder(SocketConnectorBuilder):
    _game_display_name: ClassVar[str] = "Cave Story"

    @property
    @override
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.CS

    @override
    def create_executor(self) -> CSExecutor:
        from randovania.game_connection.executor.cs_executor import CSExecutor

        return CSExecutor(self.ip)

    @override
    def create_connector(self, executor: CSExecutor) -> RemoteConnector:
        from randovania.game_connection.connector.cs_remote_connector import CSRemoteConnector

        connector = CSRemoteConnector(executor)
        connector.start_updates()
        return connector
