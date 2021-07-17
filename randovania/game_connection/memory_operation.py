import dataclasses
from typing import Optional


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
