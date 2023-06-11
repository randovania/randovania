from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_connection.connector.remote_connector import RemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.games.game import RandovaniaGame


class DebugConnectorBuilder(ConnectorBuilder):
    target_game: RandovaniaGame

    def __init__(self, game: str):
        super().__init__()
        self.target_game = RandovaniaGame(game)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DEBUG

    def configuration_params(self) -> dict:
        return {
            "game": self.target_game.value,
        }

    async def build_connector(self) -> RemoteConnector | None:
        return DebugRemoteConnector(self.target_game)

    def get_status_message(self) -> str | None:
        return self.target_game.long_name
