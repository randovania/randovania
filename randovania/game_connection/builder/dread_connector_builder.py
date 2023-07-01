import logging

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice


class DreadConnectorBuilder(ConnectorBuilder):
    _last_status_message: str | None = None

    def __init__(self, ip: str):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.ip = ip

    @property
    def pretty_text(self) -> str:
        return f"{super().pretty_text}: {self.ip}"

    async def build_connector(self) -> RemoteConnector | None:
        # Delay importing these to avoid too many early imports in startup
        from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector
        from randovania.game_connection.executor.dread_executor import DreadExecutor

        self.executor = DreadExecutor(self.ip)
        self._status_message(f"Connecting to {self.ip}")
        connect_error = await self.executor.connect()
        if connect_error is not None:
            self._status_message("Unable to connect to Dread")
            return
        self._status_message(f"Connected to {self.ip}")
        return DreadRemoteConnector(self.executor)

    def get_status_message(self) -> str | None:
        return self._last_status_message

    def _status_message(self, msg: str, log: bool = True):
        self._last_status_message = msg
        if log:
            self.logger.info(msg)
        self.StatusUpdate.emit(msg)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DREAD

    def configuration_params(self) -> dict:
        return {
            "ip": self.ip,
        }
