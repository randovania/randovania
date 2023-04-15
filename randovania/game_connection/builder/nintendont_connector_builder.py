from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor
from randovania.game_connection.memory_executor_choice import ConnectorBuilderChoice


class NintendontConnectorBuilder(PrimeConnectorBuilder):
    def __init__(self, ip: str):
        super().__init__()
        self.executor = NintendontExecutor(ip)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.NINTENDONT
