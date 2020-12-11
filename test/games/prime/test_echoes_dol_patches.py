import struct

from randovania.dol_patching.dol_file import DolFile
from randovania.games.prime import echoes_dol_patches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


def test_apply_game_options_patch(tmp_path):
    section_size = 150
    data = bytearray(b"\x00" * (0x100 + section_size))
    data[0:4] = struct.pack(">L", 0x100)
    data[0x48:0x48 + 4] = struct.pack(">L", 0x2000)
    data[0x90:0x90 + 4] = struct.pack(">L", section_size)

    tmp_path.joinpath("test.dol").write_bytes(data)
    dol_file = DolFile(tmp_path.joinpath("test.dol"))
    user_preferences = EchoesUserPreferences()
    offset = 0x2000

    # Run
    dol_file.set_editable(True)
    with dol_file:
        echoes_dol_patches.apply_game_options_patch(offset, user_preferences, dol_file)

    # Assert
    results = tmp_path.joinpath("test.dol").read_bytes()[0x100:]
    assert results == (b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                       b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x93\xe1\x00\x1c\x7c\x7f\x1b\x78'
                       b'\x38\x61\x00\x08\x38\x00\x00\x01\x90\x1f\x00\x00\x38\x00\x00\x04\x90\x1f\x00\x04'
                       b'\x38\x00\x00\x00\x90\x1f\x00\x08\x38\x00\x00\x00\x90\x1f\x00\x0c\x38\x00\x00\x00'
                       b'\x90\x1f\x00\x10\x38\x00\x00\x69\x90\x1f\x00\x14\x38\x00\x00\x4f\x90\x1f\x00\x18'
                       b'\x38\x00\x00\xff\x90\x1f\x00\x1c\x38\x00\x00\xff\x90\x1f\x00\x20\x38\x00\x00\xa0'
                       b'\x98\x1f\x00\x24\x38\x00\x00\x00\x90\x1f\x00\x2c\x90\x1f\x00\x30\x90\x1f\x00\x34'
                       b'\x60\x00\x00\x00\x60\x00\x00\x00\x60\x00\x00\x00\x60\x00\x00\x00\x60\x00\x00\x00'
                       b'\x60\x00\x00\x00\x60\x00\x00\x00')
