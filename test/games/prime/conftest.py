import struct

import pytest

from randovania.dol_patching.dol_file import DolFile


@pytest.fixture()
def dol_file(tmp_path):
    section_size = 450
    data = bytearray(b"\x00" * (0x100 + section_size))
    data[0:4] = struct.pack(">L", 0x100)
    data[0x48:0x48 + 4] = struct.pack(">L", 0x2000)
    data[0x90:0x90 + 4] = struct.pack(">L", section_size)

    tmp_path.joinpath("test.dol").write_bytes(data)
    dol_file = DolFile(tmp_path.joinpath("test.dol"))
    return dol_file
