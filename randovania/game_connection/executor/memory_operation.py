from __future__ import annotations

import dataclasses
import logging


class MemoryOperationException(Exception):
    """Exception type used for errors related to MemoryOperation's."""


@dataclasses.dataclass(frozen=True)
class MemoryOperation:
    """
    Represents an operation for reading and/or writing to the GameCube's RAM.
    Note that there are the following limits with a MemoryOperation:
    - The operation can only have one length on what to do, so if it's a read and write operation, both of their
      lengths must match (can be validated with validate_byte_size)
    - The length must be between 0 and 255, both inclusive.
    """

    address: int
    """The memory address for the operation."""
    offset: int | None = None
    """
    When offset is None, then do the operation on address as is. If it's given (even if 0), then do the
    operation on (read_4_bytes_at(address) + offset). This is useful, if you have a pointer to some struct/class.
    """
    read_byte_count: int | None = None
    """How many bytes to read, if any."""
    write_bytes: bytes | None = None
    "What bytes to write, if any."

    @property
    def byte_count(self) -> int:
        """Return the number of bytes involved in the operation. The read count is prioritized over the write count."""
        if self.read_byte_count is not None:
            return self.read_byte_count
        if self.write_bytes is not None:
            return len(self.write_bytes)
        return 0

    def validate_byte_sizes(self) -> None:
        """
        Validate that if this is a read and write operation, that their lengths are the same.
        Raises an exception if it doesn't.
        """
        if (
            self.write_bytes is not None
            and self.read_byte_count is not None
            and len(self.write_bytes) != self.read_byte_count
        ):
            raise ValueError(f"Attempting to read {self.read_byte_count} bytes while writing {len(self.write_bytes)}.")

    def __str__(self) -> str:
        """Return a readable description of this memory operation."""
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
    """Abstract executor for an interface to perform memory operations on a GameCube's RAM."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(type(self).__name__)

    async def connect(self) -> str | None:
        """Establish a connection to the target interface so that it's ready to perform operations."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Disconnect from the target interface."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Returns whether there is currently an active connection going on."""
        raise NotImplementedError

    async def perform_memory_operations(self, ops: list[MemoryOperation]) -> dict[MemoryOperation, bytes]:
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
        return result.get(op)
