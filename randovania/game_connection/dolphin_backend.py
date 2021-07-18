import dolphin_memory_engine

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.dolphin_executor import DolphinExecutor


class DolphinBackend(ConnectionBackend):
    def __init__(self):
        super().__init__(DolphinExecutor())
        self.dolphin = dolphin_memory_engine

    @property
    def name(self) -> str:
        return "Dolphin"
