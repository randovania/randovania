import asyncio
import dataclasses
import struct
from asyncio import StreamReader, StreamWriter
from typing import List, Optional

from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation
from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_description.world import World


@dataclasses.dataclass(frozen=True)
class SocketHolder:
    reader: StreamReader
    writer: StreamWriter
    api_version: int
    max_input: int
    max_output: int
    max_addresses: int


class RequestBatch:
    def __init__(self):
        self.data = b""
        self.ops = []
        self.num_read_bytes = 0
        self.addresses = []

    def copy(self) -> "RequestBatch":
        new = RequestBatch()
        new.data = self.data
        new.ops = list(self.ops)
        new.num_read_bytes = self.num_read_bytes
        new.addresses.extend(self.addresses)
        return new

    def build_request_data(self):
        header = struct.pack(f">BBBB{len(self.addresses)}I", 0, len(self.ops), len(self.addresses), 1, *self.addresses)
        return header + self.data

    @property
    def input_bytes(self):
        return len(self.data) + 4 * len(self.addresses)

    @property
    def num_validator_bytes(self):
        return 1 + (len(self.ops) - 1) // 8 if self.ops else 0

    @property
    def output_bytes(self):
        return self.num_read_bytes + self.num_validator_bytes

    def add_op(self, op: MemoryOperation):
        if op.address not in self.addresses:
            self.addresses.append(op.address)

        if op.read_byte_count is not None:
            self.num_read_bytes += op.read_byte_count

        op_byte = self.addresses.index(op.address)
        if op.read_byte_count is not None:
            op_byte = op_byte | 0x80
        if op.write_bytes is not None:
            op_byte = op_byte | 0x40
        if op.byte_count == 4:
            op_byte = op_byte | 0x20
        if op.offset is not None:
            op_byte = op_byte | 0x10

        self.data += struct.pack(">B", op_byte)
        if op.byte_count != 4:
            self.data += struct.pack(">B", op.byte_count)
        if op.offset is not None:
            self.data += struct.pack(">h", op.offset)
        if op.write_bytes is not None:
            self.data += op.write_bytes

        self.ops.append(op)


def _was_invalid_address(response: bytes, i: int) -> bool:
    return not response[i // 8] & (1 << (i % 8))


class NintendontBackend(ConnectionBackend):
    _world: Optional[World] = None
    _port = 43673
    _socket: Optional[SocketHolder] = None

    def __init__(self, ip: str):
        super().__init__()
        self._ip = ip

    @property
    def lock_identifier(self) -> Optional[str]:
        return None

    # Game Backend Stuff
    async def _connect(self) -> bool:
        if self._socket is not None:
            return True

        try:
            self._socket_error = None
            reader, writer = await asyncio.open_connection(self._ip, self._port)

            # Send API details request
            writer.write(struct.pack(f">BBBB", 1, 0, 0, 1))
            await writer.drain()

            response = await reader.read(1024)
            api_version, max_input, max_output, max_addresses = struct.unpack_from(">IIII", response, 0)

            self._socket = SocketHolder(reader, writer, api_version, max_input, max_output, max_addresses)
            return True

        except OSError as e:
            self._socket = None
            self.logger.info(f"Unable to connect to {self._ip}:{self._port}: {e}")
            self._socket_error = e

    def _prepare_requests_for(self, ops: List[MemoryOperation]) -> List[RequestBatch]:
        requests: List[RequestBatch] = []
        current_batch = RequestBatch()

        def _new_request():
            nonlocal current_batch
            requests.append(current_batch)
            current_batch = RequestBatch()

        for op in ops:
            if op.byte_count == 0:
                continue
            op.validate_byte_sizes()

            experimental = current_batch.copy()
            experimental.add_op(op)

            if (len(experimental.addresses) >= self._socket.max_addresses
                    or experimental.output_bytes > self._socket.max_output
                    or experimental.input_bytes > self._socket.max_input):
                _new_request()

            current_batch.add_op(op)

        # Finish the last batch
        _new_request()

        return requests

    async def _send_requests_to_socket(self, requests: List[RequestBatch]) -> List[bytes]:
        all_responses = []
        try:
            for request in requests:
                data = request.build_request_data()
                self.logger.info(f"Sending {data} to {self._ip, self._port}.")
                self._socket.writer.write(data)
                await self._socket.writer.drain()
                if request.output_bytes > 0:
                    response = await self._socket.reader.read(1024)
                    self.logger.info(f"Received {response}.")
                    all_responses.append(response)
                else:
                    all_responses.append(b"")

        except OSError as e:
            self.logger.info(f"Unable to connect to {self._ip}:{self._port}: {e}")
            self._socket = None
            self._socket_error = e
            raise RuntimeError("Unable to connect") from e

        return all_responses

    async def _perform_memory_operations(self, ops: List[MemoryOperation]) -> List[Optional[bytes]]:
        if self._socket is None:
            raise RuntimeError("Not connected")

        requests = self._prepare_requests_for(ops)
        all_responses = await self._send_requests_to_socket(requests)

        result = []

        for request, response in zip(requests, all_responses):
            read_index = request.num_validator_bytes
            for i, op in enumerate(request.ops):
                if op.read_byte_count is None or _was_invalid_address(response, i):
                    result.append(None)
                else:
                    result.append(response[read_index:read_index + op.read_byte_count])
                    read_index += op.read_byte_count

        return result

    async def update(self, dt: float):
        if not await self._connect():
            return

        if not await self._identify_game():
            return

        await self._send_message_from_queue(dt)

        await self._update_current_world()
        if self._world is not None:
            self._inventory = await self._get_inventory()
            if self.checking_for_collected_index:
                await self._check_for_collected_index()

    @property
    def name(self) -> str:
        return "Nintendont"

    @property
    def current_status(self) -> ConnectionStatus:
        if self._socket is None:
            return ConnectionStatus.Disconnected

        if self.patches is None:
            return ConnectionStatus.WrongGame

        if self._world is None:
            return ConnectionStatus.TitleScreen
        elif not self.checking_for_collected_index:
            return ConnectionStatus.TrackerOnly
        else:
            return ConnectionStatus.InGame
