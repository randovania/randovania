from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.memory_executor_choice import ConnectionBuilderChoice


class DolphinConnectorBuilder(PrimeConnectorBuilder):
    def __init__(self):
        super().__init__()
        self.executor = DolphinExecutor()

    @property
    def connector_builder_choice(self) -> ConnectionBuilderChoice:
        return ConnectionBuilderChoice.DOLPHIN