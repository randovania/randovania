from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.nintendont_executor import NintendontExecutor


class NintendontBackend(ConnectionBackend):
    def __init__(self, ip: str):
        super().__init__(NintendontExecutor(ip))

    @property
    def name(self) -> str:
        return "Nintendont"
