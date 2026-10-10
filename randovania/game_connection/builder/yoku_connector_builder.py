from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.builder.socket_connector_builder import SocketConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.yoku_executor import YokuExecutor


class YokuConnectorBuilder(SocketConnectorBuilder):
    _game_display_name: ClassVar[str] = "Yoku's Island Express"

    @property
    @override
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.YOKU

    @override
    def create_executor(self) -> YokuExecutor:
        from randovania.game_connection.executor.yoku_executor import YokuExecutor

        return YokuExecutor(self.ip)

    @override
    def create_connector(self, executor: YokuExecutor) -> RemoteConnector:
        from randovania.game_connection.connector.yoku_remote_connector import YokuRemoteConnector

        return YokuRemoteConnector(executor)
