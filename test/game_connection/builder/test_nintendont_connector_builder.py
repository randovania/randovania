from unittest.mock import  MagicMock
from mock import AsyncMock

import pytest
from randovania.game_connection.builder.nintendont_connector_builder import NintendontConnectorBuilder

from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor
from randovania.games.prime2.patcher import echoes_dol_versions


@pytest.fixture(name="nintendont_con_builder")
def nintendont_con_builder():
    nintendont_con_builder = NintendontConnectorBuilder("127.0.0.1")
    return nintendont_con_builder


async def test_identify_game_ntsc(nintendont_con_builder: NintendontConnectorBuilder):
    # Setup
    def side_effect(ops: list[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}
    nintendont_con_builder.executor = MagicMock(NintendontExecutor("127.0.0.1"))

    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    nintendont_con_builder.executor.perform_memory_operations.side_effect = side_effect
    nintendont_con_builder.executor.perform_single_memory_operation.return_value = build_info

    # Run
    connector = await nintendont_con_builder.build_connector()

    # Assert
    assert isinstance(connector, EchoesRemoteConnector)
    assert connector.version is echoes_dol_versions.ALL_VERSIONS[0]

async def test_is_this_version_throws_error(nintendont_con_builder: NintendontConnectorBuilder):
    # Setup
    def side_effect(ops: list[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}
    nintendont_con_builder.executor = MagicMock(NintendontExecutor("127.0.0.1"))

    nintendont_con_builder.executor.perform_memory_operations.side_effect = side_effect
    nintendont_con_builder.executor.perform_single_memory_operation.side_effect = MemoryOperationException

    # Run
    connector = await nintendont_con_builder.build_connector()
    # Assert
    assert connector is None

async def test_executor_not_connecting(nintendont_con_builder: NintendontConnectorBuilder):
    nintendont_con_builder.executor = MagicMock(NintendontExecutor("127.0.0.1"))
    nintendont_con_builder.executor.connect = AsyncMock(return_value = None)

    # Run
    connector = await nintendont_con_builder.build_connector()

    # Assert
    assert connector is None
