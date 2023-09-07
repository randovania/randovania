from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import INVALID_UUID

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector


class DebugConnectorBuilder(ConnectorBuilder):
    target_game: RandovaniaGame
    layout_uuid: uuid.UUID

    def __init__(self, game: str, layout_uuid: str = str(INVALID_UUID)):
        super().__init__()
        self.target_game = RandovaniaGame(game)
        self.layout_uuid = uuid.UUID(layout_uuid)

    @classmethod
    def create(cls, game: RandovaniaGame, layout_uuid: uuid.UUID) -> DebugConnectorBuilder:
        return cls(game.value, str(layout_uuid))

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DEBUG

    def configuration_params(self) -> dict:
        return {
            "game": self.target_game.value,
            "layout_uuid": str(self.layout_uuid),
        }

    async def build_connector(self) -> RemoteConnector | None:
        return DebugRemoteConnector(self.target_game, self.layout_uuid)

    def get_status_message(self) -> str | None:
        return f"{self.target_game.long_name}: {self.layout_uuid}"
