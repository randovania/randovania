from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor

if TYPE_CHECKING:
    from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor


class NintendontConnectorBuilder(PrimeConnectorBuilder):
    ip: str

    def __init__(self, ip: str):
        super().__init__()
        self.ip = ip

    @property
    def pretty_text(self) -> str:
        return f"{super().pretty_text}: {self.ip}"

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.NINTENDONT

    def create_executor(self) -> MemoryOperationExecutor:
        return NintendontExecutor(self.ip)

    def configuration_params(self) -> dict:
        return {
            "ip": self.ip,
        }
