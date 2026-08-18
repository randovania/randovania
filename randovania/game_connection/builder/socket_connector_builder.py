from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, override

from randovania.game_connection.builder.connector_builder import ConnectorBuilder

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector


class SocketConnectorBuilder(ConnectorBuilder):
    """Builds a connector for a game we reach over a TCP socket at a user-provided address."""

    ip: str
    _last_status_message: str | None = None

    _game_display_name: ClassVar[str]
    """How the game is named when telling the user we couldn't reach it."""

    def __init__(self, ip: str):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.ip = ip

    @property
    @override
    def pretty_text(self) -> str:
        return f"{super().pretty_text}: {self.ip}"

    def create_executor(self) -> Any:
        """Builds the executor for this game. Imports are delayed to avoid too many early imports in startup."""
        raise NotImplementedError

    def create_connector(self, executor: Any) -> RemoteConnector:
        """Builds the connector wrapping a connected executor."""
        raise NotImplementedError

    @override
    async def build_connector(self) -> RemoteConnector | None:
        self.executor = self.create_executor()
        self._status_message(f"Connecting to {self.ip}", log=False)
        connect_error = await self.executor.connect()
        if connect_error is not None:
            self._status_message(f"Unable to connect to {self._game_display_name}", log=False)
            return None
        self._status_message(f"Connected to {self.ip}")
        return self.create_connector(self.executor)

    @override
    def get_status_message(self) -> str | None:
        return self._last_status_message

    def _status_message(self, msg: str, log: bool = True) -> None:
        self._last_status_message = msg
        if log:
            self.logger.info(msg)
        self.StatusUpdate.emit(msg)

    @override
    def configuration_params(self) -> dict:
        return {
            "ip": self.ip,
        }
