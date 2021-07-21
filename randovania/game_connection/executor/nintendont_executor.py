import asyncio
import dataclasses
import struct
from asyncio import StreamReader, StreamWriter
from typing import List, Optional, Dict

from randovania.game_connection.memory_executor_choice import MemoryExecutorChoice
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperationExecutor


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

    def is_compatible_with(self, holder: SocketHolder):
        return (len(self.addresses) < holder.max_addresses
                and self.output_bytes <= holder.max_output
                and self.input_bytes <= holder.max_input)

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
    try:
        return not response[i // 8] & (1 << (i % 8))
    except IndexError:
        raise MemoryOperationException("Server response too short for validator bytes")


class NintendontExecutor(MemoryOperationExecutor):
    _port = 43673
    _socket: Optional[SocketHolder] = None
    _socket_error: Optional[Exception] = None

    def __init__(self, ip: str):
        super().__init__()
        self._ip = ip

    @property
    def ip(self):
        return self._ip

    @property
    def lock_identifier(self) -> Optional[str]:
        return None

    @property
    def backend_choice(self) -> MemoryExecutorChoice:
        return MemoryExecutorChoice.NINTENDONT

    async def connect(self) -> bool:
        if self._socket is not None:
            return True

        try:
            self._socket_error = None
            self.logger.info(f"Connecting to {self._ip}:{self._port}.")
            reader, writer = await asyncio.open_connection(self._ip, self._port)

            # Send API details request
            self.logger.info(f"Connection open, requesting API details.")

            writer.write(struct.pack(f">BBBB", 1, 0, 0, 1))
            await asyncio.wait_for(writer.drain(), timeout=30)

            self.logger.debug(f"Waiting for API details response.")
            response = await asyncio.wait_for(reader.read(1024), timeout=15)
            api_version, max_input, max_output, max_addresses = struct.unpack_from(">IIII", response, 0)

            self.logger.info(f"Remote replied with API level {api_version}, connection successful.")
            self._socket = SocketHolder(reader, writer, api_version, max_input, max_output, max_addresses)
            return True

        except (OSError, asyncio.TimeoutError, struct.error, UnicodeError) as e:
            # UnicodeError is for some invalid ip addresses
            self._socket = None
            self.logger.warning(f"Unable to connect to {self._ip}:{self._port} - ({type(e).__name__}) {e}")
            self._socket_error = e
            return False

    async def disconnect(self):
        socket = self._socket
        self._socket = None
        if socket is not None:
            socket.writer.close()

    def is_connected(self) -> bool:
        return self._socket is not None

    def _prepare_requests_for(self, ops: List[MemoryOperation]) -> List[RequestBatch]:
        requests: List[RequestBatch] = []
        current_batch = RequestBatch()

        def _new_request():
            nonlocal current_batch
            requests.append(current_batch)
            current_batch = RequestBatch()

        processes_ops = []
        max_write_size = self._socket.max_input - 20
        for i, op in enumerate(ops):
            if op.byte_count == 0:
                continue
            op.validate_byte_sizes()

            if op.read_byte_count is None and (op.write_bytes is not None
                                               and len(op.write_bytes) > max_write_size):
                self.logger.debug(f"Operation {i} had {len(op.write_bytes)} bytes, "
                                  f"above the limit of {max_write_size}. Splitting.")
                for offset in range(0, len(op.write_bytes), max_write_size):
                    if op.offset is None:
                        address = op.address + offset
                        op_offset = None
                    else:
                        address = op.address
                        op_offset = op.offset + offset
                    processes_ops.append(MemoryOperation(
                        address=address,
                        offset=op_offset,
                        write_bytes=op.write_bytes[offset:min(offset + max_write_size, len(op.write_bytes))],
                    ))
            else:
                processes_ops.append(op)

        for op in processes_ops:
            experimental = current_batch.copy()
            experimental.add_op(op)

            if not experimental.is_compatible_with(self._socket):
                _new_request()

            current_batch.add_op(op)
            if not current_batch.is_compatible_with(self._socket):
                raise ValueError(f"Request {op} is not compatible with current server.")

        # Finish the last batch
        _new_request()

        return requests

    async def _send_requests_to_socket(self, requests: List[RequestBatch]) -> List[bytes]:
        all_responses = []
        try:
            for request in requests:
                data = request.build_request_data()
                self._socket.writer.write(data)
                await self._socket.writer.drain()
                if request.output_bytes > 0:
                    response = await asyncio.wait_for(self._socket.reader.read(1024), timeout=15)
                    all_responses.append(response)
                else:
                    all_responses.append(b"")

        except (OSError, asyncio.TimeoutError) as e:
            if isinstance(e, asyncio.TimeoutError):
                self.logger.warning(f"Timeout when reading response from {self._ip}")
                self._socket_error = MemoryOperationException(f"Timeout when reading response")
            else:
                self.logger.warning(f"Unable to send {len(requests)} requests to {self._ip}:{self._port}: {e}")
                self._socket_error = MemoryOperationException(f"Unable to send {len(requests)} requests: {e}")

            await self.disconnect()
            raise self._socket_error from e

        return all_responses

    async def perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        if self._socket is None:
            raise MemoryOperationException("Not connected")

        requests = self._prepare_requests_for(ops)
        all_responses = await self._send_requests_to_socket(requests)

        result = {}

        for request, response in zip(requests, all_responses):
            read_index = request.num_validator_bytes
            for i, op in enumerate(request.ops):
                if op.read_byte_count is None:
                    continue

                if _was_invalid_address(response, i):
                    raise MemoryOperationException("Operation tried to read an invalid address")

                split = response[read_index:read_index + op.read_byte_count]
                if len(split) != op.read_byte_count:
                    raise MemoryOperationException(f"Received {len(split)} bytes, expected {op.read_byte_count}")
                else:
                    assert op not in result
                    result[op] = split

                read_index += op.read_byte_count

        return result
