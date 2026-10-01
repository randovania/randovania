from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.builder.socket_connector_builder import SocketConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.msr_executor import MSRExecutor


class MSRConnectorBuilder(SocketConnectorBuilder):
    _game_display_name: ClassVar[str] = "Samus Returns"

    @property
    @override
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.MSR

    @override
    def create_executor(self) -> MSRExecutor:
        from randovania.game_connection.executor.msr_executor import MSRExecutor

        return MSRExecutor(self.ip)

    @override
    def create_connector(self, executor: MSRExecutor) -> RemoteConnector:
        from randovania.game_connection.connector.msr_remote_connector import MSRRemoteConnector

        return MSRRemoteConnector(executor)
