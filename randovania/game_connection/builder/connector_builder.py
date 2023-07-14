from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6 import QtCore

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice


class ConnectorBuilder(QtCore.QObject):
    StatusUpdate = QtCore.Signal(str)

    @property
    def pretty_text(self) -> str:
        """Describes which builder and with what parameters it's been configured."""
        return self.connector_builder_choice.pretty_text

    async def build_connector(self) -> RemoteConnector | None:
        """Attempts to build a connector based on the rules of the concrete implementation."""
        raise NotImplementedError

    def get_status_message(self) -> str | None:
        """Returns a message indicating the status of the last build_connector call, or why it has returned None."""
        raise NotImplementedError

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        raise NotImplementedError

    def configuration_params(self) -> dict:
        raise NotImplementedError
