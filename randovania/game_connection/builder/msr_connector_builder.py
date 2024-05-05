from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector


class MSRConnectorBuilder(ConnectorBuilder):
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
        from randovania.game_connection.connector.msr_remote_connector import MSRRemoteConnector
        from randovania.game_connection.executor.msr_executor import MSRExecutor

        self.executor = MSRExecutor(self.ip)
        self._status_message(f"Connecting to {self.ip}", log=False)
        connect_error = await self.executor.connect()
        if connect_error is not None:
            self._status_message("Unable to connect to Samus Returns", log=False)
            return None
        self._status_message(f"Connected to {self.ip}")
        return MSRRemoteConnector(self.executor)

    def get_status_message(self) -> str | None:
        return self._last_status_message

    def _status_message(self, msg: str, log: bool = True) -> None:
        self._last_status_message = msg
        if log:
            self.logger.info(msg)
        self.StatusUpdate.emit(msg)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.MSR

    def configuration_params(self) -> dict:
        return {
            "ip": self.ip,
        }
