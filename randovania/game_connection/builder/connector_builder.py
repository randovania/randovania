from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.lib.signal import RdvSignal

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
    from randovania.network_client.network_client import NetworkClient


class ConnectorBuilder:
    StatusUpdate = RdvSignal[[str]]()

    enabled: bool = True

    network_client: NetworkClient | None = None
    """Set by GameConnection when the builder is added, for builders that talk to the server."""

    no_longer_usable: bool = False
    """
    Set by a builder that will never be able to build a connector again, so that GameConnection discards
    it instead of retrying forever.
    """

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
