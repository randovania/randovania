import pytest
from mock import AsyncMock

from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation


@pytest.fixture(name="connector")
def corruption_remote_connector():
    from randovania.games.prime import corruption_dol_versions
    connector = CorruptionRemoteConnector(corruption_dol_versions.ALL_VERSIONS[0])
    return connector


@pytest.mark.parametrize("correct_vtable", [False, True])
@pytest.mark.parametrize("has_cplayer", [False, True])
@pytest.mark.parametrize("has_pending_op", [False, True])
@pytest.mark.parametrize("has_world", [False, True])
@pytest.mark.asyncio
async def test_fetch_game_status(connector: CorruptionRemoteConnector, has_world, has_pending_op,
                                 has_cplayer, correct_vtable):
    # Setup
    expected_world = connector.game.world_list.worlds[1]

    cplayer_address = 0x8099FFAA

    executor = AsyncMock()
    executor.perform_memory_operations.side_effect = lambda ops: {
        ops[0]: expected_world.world_asset_id.to_bytes(8, "big") if has_world else b"DEADBEEF",
        ops[1]: b"\x01" if has_pending_op else b"\x00",
        ops[2]: cplayer_address.to_bytes(4, "big") if has_cplayer else None,
    }

    if correct_vtable:
        vtable_memory_return = connector.version.cplayer_vtable.to_bytes(4, "big")
    else:
        vtable_memory_return = b"CAFE"
    executor.perform_single_memory_operation.return_value = vtable_memory_return

    # Run
    actual_has_op, actual_world = await connector.current_game_status(executor)

    # Assert
    if has_world and has_cplayer and correct_vtable:
        assert actual_world is expected_world
    else:
        assert actual_world is None
    assert actual_has_op == has_pending_op
    if has_cplayer:
        executor.perform_single_memory_operation.assert_awaited_once_with(MemoryOperation(
            cplayer_address, read_byte_count=4,
        ))
    else:
        executor.perform_single_memory_operation.assert_not_awaited()
