from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor


class DolphinConnectorBuilder(PrimeConnectorBuilder):
    def __init__(self):
        super().__init__()
        self.executor = DolphinExecutor()
