from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.executor import yoku_executor
from randovania.game_connection.executor.yoku_executor import YokuExecutor, YokuLuaException
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex

LAYOUT_UUID = "00000000-0000-1111-0000-000000000000"
LOCATION_COUNT = 248
INVENTORY_SIZE = 51


@pytest.fixture(name="executor")
def yoku_executor_fixture():
    return YokuExecutor("127.0.0.1")


def lua_exchange(request_number: int, payload: bytes, success: bool = True) -> list[bytes]:
    """The reads a single remote lua execution performs: packet type, request number, header, then payload."""
    header = bytes([int(success)]) + len(payload).to_bytes(4, "little")
    return [b"\x03", bytes([request_number]), header, payload]


def handshake_answers(api_details: bytes) -> list[bytes]:
    return [b"\x01", b"\x00", *lua_exchange(1, api_details)]


def bootstrap_answers(accepted: int = LOCATION_COUNT) -> list[bytes]:
    return [
        *lua_exchange(2, b""),  # RL.SetInventoryItems
        *lua_exchange(3, b""),  # RL.SetIdentifier
        *lua_exchange(4, str(accepted).encode()),  # RL.SetLocations
    ]


def _connection(mocker, answers: list[bytes]) -> tuple[MagicMock, MagicMock]:
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(side_effect=answers)
    mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))
    return reader, writer


def _sent_lua(writer: MagicMock) -> list[str]:
    """The lua code of every remote lua execution packet written, in order."""
    packets = [written.args[0] for written in writer.write.call_args_list]
    return [packet[5:].decode("utf-8") for packet in packets if packet[0] == 3]


async def test_connect(executor: YokuExecutor, mocker):
    executor.read_loop = MagicMock()
    mocker.patch("asyncio.get_event_loop", new_callable=MagicMock, return_value=MagicMock(asyncio.AbstractEventLoop))
    _, writer = _connection(mocker, handshake_answers(f"1,4096,{LAYOUT_UUID}".encode()) + bootstrap_answers())

    ret = await executor.connect()

    assert ret is None
    assert executor.is_connected()
    assert executor.layout_uuid_str == LAYOUT_UUID
    assert writer.write.call_args_list[0].args[0] == b"\x01\x02"  # handshake, multiworld interest

    inventory, identifier, locations = _sent_lua(writer)[1:]
    assert inventory.startswith('return RL.SetInventoryItems("abilities/dive,abilities/dive_speed,')
    assert inventory.count(",") == INVENTORY_SIZE - 1
    assert identifier == f'RL.SetIdentifier("uuid:{LAYOUT_UUID}")'
    assert locations.startswith('return RL.SetLocations("21042450,21042661,')
    assert locations.count(",") == LOCATION_COUNT - 1


async def test_connect_skips_other_packets(executor: YokuExecutor, mocker):
    executor.read_loop = MagicMock()
    executor.signals = MagicMock()
    mocker.patch("asyncio.get_event_loop", new_callable=MagicMock, return_value=MagicMock(asyncio.AbstractEventLoop))
    answers = handshake_answers(f"1,4096,{LAYOUT_UUID}".encode())
    # A packet the game pushes on its own while the handshake waits for an answer is still handled
    answers[2:2] = [b"\x05", b"\x02\x00\x00\x00", b"{}"]
    _connection(mocker, answers + bootstrap_answers())

    assert await executor.connect() is None
    assert executor.is_connected()
    executor.signals.new_inventory.emit.assert_called_once_with("{}")


async def test_connect_no_save_loaded(executor: YokuExecutor, mocker):
    _, writer = _connection(mocker, handshake_answers(b"1,4096,"))

    ret = await executor.connect()

    assert ret == "No Randovania save is loaded in Yoku's Island Express."
    assert executor._socket is None
    writer.close.assert_called_once_with()
    assert len(_sent_lua(writer)) == 1  # no bootstrap


async def test_connect_wrong_api_version(executor: YokuExecutor, mocker):
    _connection(mocker, handshake_answers(f"2,4096,{LAYOUT_UUID}".encode()))

    ret = await executor.connect()

    assert ret == (
        "The game's API version doesn't match (API version 2, needs 1). "
        "Export the game again with this Randovania version."
    )
    assert executor._socket is None


async def test_connect_locations_refused(executor: YokuExecutor, mocker):
    _connection(mocker, handshake_answers(f"1,4096,{LAYOUT_UUID}".encode()) + bootstrap_answers(accepted=10))

    ret = await executor.connect()

    assert ret == (
        f"Unable to connect to 127.0.0.1:6970 - (YokuLuaException) The game accepted 10 of {LOCATION_COUNT} locations"
    )
    assert executor._socket is None
    assert isinstance(executor._socket_error, YokuLuaException)


async def test_connect_fail_lua_error(executor: YokuExecutor, mocker):
    answers = handshake_answers(f"1,4096,{LAYOUT_UUID}".encode()) + lua_exchange(2, b"error", success=False)
    _connection(mocker, answers)

    ret = await executor.connect()

    assert ret == "Unable to connect to 127.0.0.1:6970 - (YokuLuaException) "
    assert executor._socket is None


async def test_connect_connection_closed(executor: YokuExecutor, mocker):
    _connection(mocker, [b""])

    ret = await executor.connect()

    assert ret == "Unable to connect to 127.0.0.1:6970 - (OSError) missing packet type"
    assert executor._socket is None


async def test_handshake_timeout(executor: YokuExecutor, mocker):
    async def never(*args):
        await asyncio.Event().wait()

    mocker.patch.object(YokuExecutor, "_handshake_timeout", 0.01)
    reader, _ = _connection(mocker, [])
    reader.read = never

    ret = await executor.connect()

    assert ret == "Unable to connect to 127.0.0.1:6970 - (TimeoutError) "
    assert executor._socket is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain", '"plain"'),
        ('a "quote"', '"a \\"quote\\""'),
        ("back\\slash", '"back\\\\slash"'),
        ("two\r\nlines", '"two\\r\\nlines"'),
    ],
)
def test_lua_string(value: str, expected: str):
    assert yoku_executor.lua_string(value) == expected


def test_location_ids():
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)

    locations = yoku_executor.location_ids(game)

    assert len(locations) == LOCATION_COUNT
    assert len(set(locations)) == LOCATION_COUNT
    node = game.region_list.node_from_pickup_index(PickupIndex(0))
    assert locations[0] == (node.extra["level_number"] << 16) | node.extra["object_id"]


def test_inventory_item_ids():
    game = default_database.game_description_for(RandovaniaGame.YOKUS_ISLAND_EXPRESS)

    items = yoku_executor.inventory_item_ids(game)

    assert len(items) == INVENTORY_SIZE
    assert items[:2] == ["abilities/dive", "abilities/dive_speed"]
    assert items[-1] == "reward_fruit_medium"
