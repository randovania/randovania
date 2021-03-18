import dataclasses
import struct
from pathlib import Path
from typing import Tuple, Optional, BinaryIO, Iterable, List, Dict, Union

from randovania.dol_patching import assembler

_NUM_TEXT_SECTIONS = 7
_NUM_DATA_SECTIONS = 11
_NUM_SECTIONS = _NUM_TEXT_SECTIONS + _NUM_DATA_SECTIONS


@dataclasses.dataclass(frozen=True)
class Section:
    offset: int
    base_address: int
    size: int

    def is_empty(self):
        return self.size == 0


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

    def as_bytes(self) -> bytes:
        args = []
        args.extend(section.offset for section in self.sections)
        args.extend(section.base_address for section in self.sections)
        args.extend(section.size for section in self.sections)
        args.extend([self.bss_address, self.bss_size, self.entry_point])

        return struct.pack(f">{_NUM_SECTIONS}L{_NUM_SECTIONS}L{_NUM_SECTIONS}LLLL", *args) + (b"\x00" * 0x1C)

    def section_for_address(self, address: int) -> Optional[Section]:
        for section in self.sections:
            relative_to_base = address - section.base_address
            if 0 <= relative_to_base < section.size:
                return section

    def offset_for_address(self, address: int) -> Optional[int]:
        section = self.section_for_address(address)
        if section is not None:
            return section.offset + (address - section.base_address)
        return None


class DolFile:
    header: DolHeader
    symbols: Dict[str, int]
    dol_file: Optional[BinaryIO] = None
    editable: bool = False

    def __init__(self, dol_path: Path):
        with dol_path.open("rb") as f:
            header_bytes = f.read(0x100)

        self.dol_path = dol_path
        self.header = DolHeader.from_bytes(header_bytes)
        self.symbols = {}

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

    def resolve_symbol(self, address_or_symbol: Union[int, str]) -> int:
        if isinstance(address_or_symbol, str):
            return self.symbols[address_or_symbol]
        else:
            return address_or_symbol

    def offset_for_address(self, address: int) -> int:
        offset = self.header.offset_for_address(address)
        if offset is None:
            raise ValueError(f"Address 0x{address:x} could not be resolved for dol at {self.dol_file}")
        return offset

    def read(self, address: int, size: int) -> bytes:
        offset = self.offset_for_address(address)
        self.dol_file.seek(offset)
        return self.dol_file.read(size)

    def write(self, address_or_symbol: Union[int, str], code_points: Iterable[int]):
        offset = self.offset_for_address(self.resolve_symbol(address_or_symbol))
        self.dol_file.seek(offset)
        self.dol_file.write(bytes(code_points))

    def write_instructions(self, address_or_symbol: Union[int, str],
                           instructions: List[assembler.BaseInstruction]):
        address = self.resolve_symbol(address_or_symbol)
        self.write(address, assembler.assemble_instructions(address, instructions, symbols=self.symbols))

    def _check_for_overlapping_segment(self, address: int, size: int):
        if (self.header.section_for_address(address) is not None
                or self.header.section_for_address(address + size) is not None):
            raise ValueError(f"New segment at {address:x} with size {size} overlaps with existing segments")

    def add_text_section(self, address: int, data: bytes):
        if len(data) & 0x1f != 0:
            raise ValueError(f"Invalid length for new text ({len(data)}) - not 32 byte aligned")
        self._check_for_overlapping_segment(address, len(data))
        try:
            index = next(i for i, section in enumerate(self.header.sections[:_NUM_TEXT_SECTIONS]) if section.is_empty())
        except StopIteration:
            raise ValueError("No empty sections available")

        self.dol_file.seek(0, 2)
        offset = self.dol_file.tell()
        self.dol_file.write(data)

        sections = list(self.header.sections)
        sections[index] = Section(
            offset=offset,
            base_address=address,
            size=len(data),
        )
        self.header = dataclasses.replace(self.header, sections=tuple(sections))
        self.dol_file.seek(0, 0)
        self.dol_file.write(self.header.as_bytes())
