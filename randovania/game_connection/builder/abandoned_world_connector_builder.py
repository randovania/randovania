from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector.abandoned_world_remote_connector import AbandonedWorldRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.layout.versioned_preset import VersionedPreset
from randovania.network_client.network_client import ConnectionState, UnableToConnect
from randovania.network_common import error

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector

# How long to wait before contacting the server again after a failed attempt.
_RETRY_INTERVAL_SECONDS = 30.0


class AbandonedWorldConnectorBuilder(ConnectorBuilder):
    """
    Builds an `AbandonedWorldRemoteConnector` for an abandoned world, by downloading the data the connector needs
    (the world's own game modifications and its collected locations) from the server.

    Requires the network client to be connected and the logged user to claim the world.
    """

    target_game: RandovaniaGame
    layout_uuid: uuid.UUID

    def __init__(self, game: str, layout_uuid: str):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)
        self.target_game = RandovaniaGame(game)
        self.layout_uuid = uuid.UUID(layout_uuid)
        self._status_message: str | None = None
        self._next_attempt = 0.0

    @classmethod
    def create(cls, game: RandovaniaGame, layout_uuid: uuid.UUID) -> AbandonedWorldConnectorBuilder:
        return cls(game.value, str(layout_uuid))

    @property
    def pretty_text(self) -> str:
        return f"{super().pretty_text}: {self.target_game.long_name}"

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.ABANDONED

    def configuration_params(self) -> dict:
        return {
            "game": self.target_game.value,
            "layout_uuid": str(self.layout_uuid),
        }

    async def build_connector(self) -> RemoteConnector | None:
        network_client = self.network_client
        if network_client is None or network_client.connection_state != ConnectionState.Connected:
            self._status_message = "Waiting for a connection to the server."
            return None

        if time.monotonic() < self._next_attempt:
            return None

        try:
            data = await network_client.get_abandoned_world_data(self.layout_uuid)
        except error.WorldNotAssociatedError:
            self.logger.info("No longer claiming abandoned world %s; discarding its builder.", self.layout_uuid)
            self.no_longer_usable = True
            return None

        except (error.BaseNetworkError, UnableToConnect) as e:
            self.logger.info("Unable to get abandoned world data for %s: %s", self.layout_uuid, e)
            self._status_message = f"Unable to get world data from the server: {e}"
            self._next_attempt = time.monotonic() + _RETRY_INTERVAL_SECONDS
            return None

        self._status_message = None
        return AbandonedWorldRemoteConnector(
            self.layout_uuid,
            VersionedPreset.from_str(data["preset_raw"]),
            data["order"],
            data["game_modifications"],
            data["collected_locations"],
        )

    def get_status_message(self) -> str | None:
        return self._status_message
