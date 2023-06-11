from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice


class DolphinConnectorBuilder(PrimeConnectorBuilder):
    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DOLPHIN

    def create_executor(self) -> MemoryOperationExecutor:
        return DolphinExecutor()

    def configuration_params(self) -> dict:
        return {}
