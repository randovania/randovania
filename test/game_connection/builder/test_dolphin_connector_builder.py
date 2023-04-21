from unittest.mock import  MagicMock

import pytest
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder

from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import MemoryOperation
from randovania.games.prime2.patcher import echoes_dol_versions


@pytest.fixture(name="dolphin_con_builder")
def dolphin_con_builder():
    dolphin_con_builder = PrimeConnectorBuilder()
    return dolphin_con_builder


async def test_identify_game_ntsc(dolphin_con_builder: DolphinConnectorBuilder):
    # Setup
    def side_effect(ops: list[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}
    dolphin_con_builder.executor = MagicMock(DolphinExecutor())

    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    dolphin_con_builder.executor.perform_memory_operations.side_effect = side_effect
    dolphin_con_builder.executor.perform_single_memory_operation.return_value = build_info

    # Run
    connector = await dolphin_con_builder.build_connector()

    # Assert
    assert isinstance(connector, EchoesRemoteConnector)
    assert connector.version is echoes_dol_versions.ALL_VERSIONS[0]


async def test_identify_game_error(dolphin_con_builder: DolphinConnectorBuilder):
    # Setup
    dolphin_con_builder.executor = MagicMock(DolphinExecutor())
    dolphin_con_builder.executor.perform_memory_operations.side_effect = RuntimeError("not connected")

    # Run
    assert not await dolphin_con_builder.build_connector()
