from __future__ import annotations

import dataclasses
import logging
from collections.abc import Sequence
from typing import TypeGuard


class MemoryOperationException(Exception):
    """Exception type used for errors related to MemoryOperation's."""


@dataclasses.dataclass(frozen=True)
class MemoryOperation:
    """An abstract class representing an operation for dealing with the GameCube's RAM."""

    address: int
    """The memory address for the operation."""
    offset: int | None = None
    """
    When offset is None, then do the operation on address as is. If it's given (even if 0), then do the
    operation on (read_4_bytes_at(address) + offset). This is useful, if you have a pointer to some struct/class.
    """

    @property
    def byte_count(self) -> int:
        """Return the number of bytes involved in the operation."""
        raise NotImplementedError

    @staticmethod
    def is_read_op(instance: MemoryOperation) -> TypeGuard[MemoryReadOperation]:
        """Type guards on whether a given instance is a reading operation."""
        return isinstance(instance, MemoryReadOperation)

    @staticmethod
    def is_write_op(instance: MemoryOperation) -> TypeGuard[MemoryWriteOperation]:
        """Type guards on whether a given instance is a writing operation."""
        return isinstance(instance, MemoryWriteOperation)

    def __str__(self) -> str:
        address_text = f"0x{self.address:08x}"
        if self.offset is not None:
            address_text = f"*{address_text} {self.offset:+05x}"

        return address_text


@dataclasses.dataclass(frozen=True)
class MemoryReadOperation(MemoryOperation):
    """Represents an operation to read from the GameCube's RAM. Note, that reading has a limit of 255 bytes."""

    count: int = 0
    """How many bytes to read."""

    def __post_init__(self) -> None:
        if not (0 <= self.count <= 255):
            raise ValueError("A read operation can only be between 0 and 255, inclusive.")

    @property
    def byte_count(self) -> int:
        return self.count

    def __str__(self) -> str:
        address_text = super().__str__()

        return f"At {address_text}, read {self.count} bytes"


@dataclasses.dataclass(frozen=True)
class MemoryWriteOperation(MemoryOperation):
    """Represents an operation to write to the GameCube's RAM. Note, that writing has a limit of 255 bytes."""

    data: bytes = b""
    "What bytes to write."

    def __post_init__(self) -> None:
        if not (0 <= len(self.data) <= 255):
            raise ValueError("A write operation's length can only be between 0 and 255, inclusive.")

    @property
    def byte_count(self) -> int:
        return len(self.data)

    def __str__(self) -> str:
        address_text = super().__str__()

        return f"At {address_text}, write {self.data.hex()}"


class MemoryOperationExecutor:
    """Abstract executor for an interface to perform memory operations on a GameCube's RAM."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(type(self).__name__)

    @property
    def max_output(self) -> int:
        raise NotImplementedError

    @property
    def max_input(self) -> int:
        raise NotImplementedError

    async def connect(self) -> str | None:
        """Establish a connection to the target interface so that it's ready to perform operations."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Disconnect from the target interface."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Returns whether there is currently an active connection going on."""
        raise NotImplementedError

    async def perform_memory_operations(self, ops: Sequence[MemoryOperation]) -> dict[MemoryReadOperation, bytes]:
        """Execute given memory operations.

        Args:
            ops: The list of memory operations to execute.

        Returns:
            A mapping from each MemoryOperation to its read result bytes.
            Only read operations will be present, write operations will not.
        """
        raise NotImplementedError

    async def perform_single_memory_operation(self, op: MemoryOperation) -> bytes | None:
        """
        Execute a single memory operation and return its result.
        If it was a write operation, it will return None instead.
        """
        result = await self.perform_memory_operations([op])
        if MemoryOperation.is_read_op(op):
            return result[op]
        return None
