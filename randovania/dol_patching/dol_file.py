import dataclasses
import struct
from pathlib import Path
from typing import Tuple, Optional, BinaryIO, Iterable

from randovania.dol_patching import assembler

_NUM_TEXT_SECTIONS = 7
_NUM_DATA_SECTIONS = 11
_NUM_SECTIONS = _NUM_TEXT_SECTIONS + _NUM_DATA_SECTIONS


@dataclasses.dataclass(frozen=True)
class Section:
    offset: int
    base_address: int
    size: int


@dataclasses.dataclass(frozen=True)
class DolHeader:
    sections: Tuple[Section, ...]
    bss_address: int
    bss_size: int
    entry_point: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "DolHeader":
        struct_format = f">{_NUM_SECTIONS}L"
        offset_for_section = struct.unpack_from(struct_format, data, 0)
        base_address_for_section = struct.unpack_from(struct_format, data, 0x48)
        size_for_section = struct.unpack_from(struct_format, data, 0x90)

        bss_address, bss_size, entry_point = struct.unpack_from(">LLL", data, 0xD8)
        sections = tuple(Section(offset_for_section[i], base_address_for_section[i], size_for_section[i])
                         for i in range(_NUM_SECTIONS))

        return cls(sections, bss_address, bss_size, entry_point)

    def offset_for_address(self, address: int) -> Optional[int]:
        for section in self.sections:
            relative_to_base = address - section.base_address
            if 0 <= relative_to_base < section.size:
                return section.offset + relative_to_base

        return None


class DolFile:
    dol_file: Optional[BinaryIO] = None
    editable: bool = False

    def __init__(self, dol_path: Path):
        with dol_path.open("rb") as f:
            header_bytes = f.read(0x100)

        self.dol_path = dol_path
        self.header = DolHeader.from_bytes(header_bytes)

    def set_editable(self, editable: bool):
        self.editable = editable

    def __enter__(self):
        if self.editable:
            f = self.dol_path.open("r+b")
        else:
            f = self.dol_path.open("rb")
        self.dol_file = f.__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dol_file.__exit__(exc_type, exc_type, exc_tb)
        self.dol_file = None

    def offset_for_address(self, address: int) -> int:
        offset = self.header.offset_for_address(address)
        if offset is None:
            raise ValueError(f"Address 0x{address:x} could not be resolved for dol at {self.dol_file}")
        return offset

    def read(self, address: int, size: int) -> bytes:
        offset = self.offset_for_address(address)
        self.dol_file.seek(offset)
        return self.dol_file.read(size)

    def write(self, address: int, code_points: Iterable[int]):
        offset = self.offset_for_address(address)
        self.dol_file.seek(offset)
        self.dol_file.write(bytes(code_points))

    def write_instructions(self, address: int, instructions: Iterable[assembler.BaseInstruction]):
        self.write(address, assembler.assemble_instructions(address, instructions))
