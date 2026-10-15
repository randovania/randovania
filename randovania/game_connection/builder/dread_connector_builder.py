from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.builder.socket_connector_builder import SocketConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.dread_executor import DreadExecutor


class DreadConnectorBuilder(SocketConnectorBuilder):
    _game_display_name: ClassVar[str] = "Dread"

    @property
    @override
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DREAD

    @override
    def create_executor(self) -> DreadExecutor:
        from randovania.game_connection.executor.dread_executor import DreadExecutor

        return DreadExecutor(self.ip)

    @override
    def create_connector(self, executor: DreadExecutor) -> RemoteConnector:
        from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector

        return DreadRemoteConnector(executor)
