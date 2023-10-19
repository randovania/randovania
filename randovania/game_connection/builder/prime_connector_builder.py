from __future__ import annotations

import importlib
import importlib.util
import logging
from typing import TYPE_CHECKING

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.executor.memory_operation import (
    MemoryOperation,
    MemoryOperationException,
    MemoryOperationExecutor,
)

if TYPE_CHECKING:
    from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice


class PrimeConnectorBuilder(ConnectorBuilder):
    _last_status_message: str | None = None

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(type(self).__name__)

    def create_executor(self) -> MemoryOperationExecutor:
        raise NotImplementedError

    def get_status_message(self) -> str | None:
        return self._last_status_message

    async def build_connector(self) -> RemoteConnector | None:
        if importlib.util.find_spec("open_prime_rando") is None:
            self._status_message("open_prime_rando not installed", log=False)
            return None

        # Delay importing these to avoid too many early imports in startup
        from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions
        from open_prime_rando.dol_patching.echoes import dol_versions as echoes_dol_versions
        from open_prime_rando.dol_patching.prime1 import dol_versions as prime1_dol_versions

        from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
        from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
        from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector

        executor = self.create_executor()

        self._status_message("Connecting...", log=False)
        connect_error = await executor.connect()
        if connect_error is not None:
            self._status_message(connect_error, log=False)
            return None

        self._status_message("Identifying game...", log=False)
        all_connectors: list[PrimeRemoteConnector] = [
            Prime1RemoteConnector(version, executor) for version in prime1_dol_versions.ALL_VERSIONS
        ]
        all_connectors.extend(
            [EchoesRemoteConnector(version, executor) for version in echoes_dol_versions.ALL_VERSIONS]
        )
        all_connectors.extend(
            [CorruptionRemoteConnector(version, executor) for version in corruption_dol_versions.ALL_VERSIONS]
        )
        read_first_ops = [
            MemoryOperation(
                connectors.version.build_string_address, read_byte_count=min(len(connectors.version.build_string), 4)
            )
            for connectors in all_connectors
        ]
        try:
            first_ops_result = await executor.perform_memory_operations(read_first_ops)
        except (RuntimeError, MemoryOperationException) as e:
            self._status_message(f"Unable to probe for game version: {e}")
            executor.disconnect()
            return None

        possible_connectors: list[PrimeRemoteConnector] = [
            connector
            for connector, read_op in zip(all_connectors, read_first_ops)
            if first_ops_result.get(read_op) == connector.version.build_string[:4]
        ]

        for connector in possible_connectors:
            try:
                is_version = await connector.check_for_world_uid()
            except (RuntimeError, MemoryOperationException) as e:
                self._status_message(e)
                executor.disconnect()
                return None

            if is_version:
                self._status_message(f"identified game as {connector.description()}")
                connector.start_updates()
                return connector

        self._status_message("Could not identify which game it is")
        executor.disconnect()
        return None

    def _status_message(self, msg: str, log: bool = True):
        self._last_status_message = msg
        if log:
            self.logger.info(msg)
        self.StatusUpdate.emit(msg)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        raise NotImplementedError

    def configuration_params(self) -> dict:
        raise NotImplementedError
