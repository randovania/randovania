from mock import AsyncMock

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException, \
    MemoryOperationExecutor
from randovania.games.prime2.patcher import echoes_dol_versions
from mock import AsyncMock

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException, \
    MemoryOperationExecutor
from randovania.games.prime2.patcher import echoes_dol_versions


class MockedPrimeConnectorBuilder(PrimeConnectorBuilder):
    def __init__(self):
        super().__init__()
        self.executor = AsyncMock()

    def create_executor(self) -> MemoryOperationExecutor:
        return self.executor

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.DOLPHIN

    def configuration_params(self) -> dict:
        pass


async def test_identify_game_ntsc():
    # Setup
    def side_effect(ops: list[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}

    con_builder = MockedPrimeConnectorBuilder()

    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    con_builder.executor.connect.return_value = None
    con_builder.executor.perform_memory_operations.side_effect = side_effect
    con_builder.executor.perform_single_memory_operation.return_value = build_info

    # Run
    connector = await con_builder.build_connector()

    # Assert
    assert isinstance(connector, EchoesRemoteConnector)
    assert connector.version is echoes_dol_versions.ALL_VERSIONS[0]


async def test_is_this_version_throws_error():
    # Setup
    def side_effect(ops: list[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}

    con_builder = MockedPrimeConnectorBuilder()

    con_builder.executor.perform_memory_operations.side_effect = side_effect
    con_builder.executor.perform_single_memory_operation.side_effect = MemoryOperationException

    # Run
    connector = await con_builder.build_connector()
    # Assert
    assert connector is None


async def test_executor_not_connecting():
    con_builder = MockedPrimeConnectorBuilder()
    con_builder.executor.connect = AsyncMock(return_value="Unable to connect")

    # Run
    connector = await con_builder.build_connector()

    # Assert
    assert connector is None
