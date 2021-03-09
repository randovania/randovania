import struct

import pytest

from randovania.dol_patching.dol_file import DolFile, DolHeader, Section, _NUM_SECTIONS


@pytest.fixture()
def dol_file(tmp_path):
    section_size = 0x1C2
    sections = [Section(0, 0, 0)] * _NUM_SECTIONS
    sections[0] = Section(0x100, base_address=0x2000, size=section_size)

    data = bytearray(b"\x00" * (0x100 + section_size))
    data[0:0x100] = DolHeader(tuple(sections), 0, 0, 0).as_bytes()

    tmp_path.joinpath("test.dol").write_bytes(data)
    dol_file = DolFile(tmp_path.joinpath("test.dol"))
    return dol_file
