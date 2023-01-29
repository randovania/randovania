import logging

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.connector.prime1_remote_connector import Prime1RemoteConnector
from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
from randovania.game_connection.connector.remote_connector_v2 import RemoteConnectorV2
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException, \
    MemoryOperationExecutor
from randovania.games.prime1.patcher import prime1_dol_versions
from randovania.games.prime2.patcher import echoes_dol_versions
from randovania.games.prime3.patcher import corruption_dol_versions


class PrimeConnectorBuilder(ConnectorBuilder):
    executor: MemoryOperationExecutor

    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    async def build_connector(self) -> RemoteConnectorV2 | None:
        all_connectors: list[PrimeRemoteConnector] = [
            Prime1RemoteConnector(version)
            for version in prime1_dol_versions.ALL_VERSIONS
        ]
        all_connectors.extend([
            EchoesRemoteConnector(version)
            for version in echoes_dol_versions.ALL_VERSIONS
        ])
        all_connectors.extend([
            CorruptionRemoteConnector(version)
            for version in corruption_dol_versions.ALL_VERSIONS
        ])
        read_first_ops = [
            MemoryOperation(connectors.version.build_string_address,
                            read_byte_count=min(len(connectors.version.build_string), 4))
            for connectors in all_connectors
        ]
        try:
            first_ops_result = await self.executor.perform_memory_operations(read_first_ops)
        except (RuntimeError, MemoryOperationException) as e:
            self.logger.debug(f"Unable to probe for game version: {e}")
            return None

        possible_connectors: list[PrimeRemoteConnector] = [
            connectors
            for connectors, read_op in zip(all_connectors, read_first_ops)
            if first_ops_result.get(read_op) == connectors.version.build_string[:4]
        ]

        for connector in possible_connectors:
            try:
                is_version = await connector.is_this_version(self.executor)
            except (RuntimeError, MemoryOperationException) as e:
                return None

            if is_version:
                self.logger.info(f"identified game as {connector.description()}")
                return connector
