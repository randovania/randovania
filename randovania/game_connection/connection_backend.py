from typing import Optional

from randovania.game_connection.connection_base import ConnectionBase


class ConnectionBackend(ConnectionBase):
    _checking_for_collected_index: bool = False

    @property
    def name(self) -> str:
        raise NotImplementedError()

    async def update(self, dt: float):
        raise NotImplementedError()

    @property
    def lock_identifier(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def checking_for_collected_index(self):
        return self._checking_for_collected_index

    @checking_for_collected_index.setter
    def checking_for_collected_index(self, value):
        self._checking_for_collected_index = value
