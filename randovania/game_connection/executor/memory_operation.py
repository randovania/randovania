import dataclasses
import logging
from typing import Optional, List, Dict

from randovania.game_connection.memory_executor_choice import MemoryExecutorChoice


class MemoryOperationException(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class MemoryOperation:
    address: int
    offset: Optional[int] = None
    read_byte_count: Optional[int] = None
    write_bytes: Optional[bytes] = None

    @property
    def byte_count(self) -> int:
        if self.read_byte_count is not None:
            return self.read_byte_count
        if self.write_bytes is not None:
            return len(self.write_bytes)
        return 0

    def validate_byte_sizes(self):
        if (self.write_bytes is not None
                and self.read_byte_count is not None
                and len(self.write_bytes) != self.read_byte_count):
            raise ValueError(f"Attempting to read {self.read_byte_count} bytes while writing {len(self.write_bytes)}.")

    def __str__(self):
        address_text = f"0x{self.address:08x}"
        if self.offset is not None:
            address_text = f"*{address_text} {self.offset:+05x}"

        operation_pretty = []
        if self.read_byte_count is not None:
            operation_pretty.append(f"read {self.read_byte_count} bytes")
        if self.write_bytes is not None:
            operation_pretty.append(f"write {self.write_bytes.hex()}")

        return f"At {address_text}, {' and '.join(operation_pretty)}"


class MemoryOperationExecutor:
    def __init__(self):
        self.logger = logging.getLogger(type(self).__name__)

    @property
    def lock_identifier(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def backend_choice(self) -> MemoryExecutorChoice:
        raise NotImplementedError()

    async def connect(self) -> bool:
        raise NotImplementedError()

    async def disconnect(self):
        raise NotImplementedError()

    def is_connected(self) -> bool:
        raise NotImplementedError()

    async def perform_memory_operations(self, ops: List[MemoryOperation]) -> Dict[MemoryOperation, bytes]:
        raise NotImplementedError()

    async def perform_single_memory_operation(self, op: MemoryOperation) -> Optional[bytes]:
        result = await self.perform_memory_operations([op])
        return result.get(op)
