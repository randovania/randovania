from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector.remote_connector_v2 import RemoteConnectorV2
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor


class NintendontConnectorBuilder(PrimeConnectorBuilder):
    def __init__(self, ip: str):
        super().__init__()
        self.executor = NintendontExecutor(ip)

    async def build_connector(self) -> RemoteConnectorV2 | None:
        if not await self.executor.connect():
            return None
        return await super().build_connector()
