from pathlib import Path
from typing import BinaryIO

from randovania.interface_common.cosmetic_patches import CosmeticPatches

_GC_NTSC_DOL_VERSION = 0x003A22A0


def _apply_string_display_patch(binary_version: int, dol_file: BinaryIO):
    patch_for_binary_versions = {
        _GC_NTSC_DOL_VERSION: {
            "message_receiver_offset": 0x34E20,
            "message_receiver_string_ref": [0x80, 0x3a, 0x63, 0x80],
            "wstring_constructor": [0x80, 0x2f, 0xf3, 0xdc],
            "display_hud_memo": [0x80, 0x06, 0xb3, 0xc8],
        }
    }
    patches = patch_for_binary_versions[binary_version]

    message_receiver_string_ref = patches["message_receiver_string_ref"]
    address_wstring_constructor = patches["wstring_constructor"]
    address_display_hud_memo = patches["display_hud_memo"]

    message_receiver_patch = bytes([
        0x94, 0x21, 0xFF, 0xD4,
        0x7C, 0x08, 0x02, 0xA6,
        0x90, 0x01, 0x00, 0x30,
        0x88, 0x83, 0x00, 0x02,
        0x2C, 0x04, 0x00, 0x00,
        0x41, 0x82, 0x00, 0x60,
        0x38, 0xC0, 0x00, 0x00,
        0x98, 0xC3, 0x00, 0x02,
        0x3C, 0xA0, 0x41, 0x00,
        0x38, 0xE0, 0x00, 0x01,
        0x39, 0x20, 0x00, 0x09,
        0x90, 0xA1, 0x00, 0x10,
        0x98, 0xE1, 0x00, 0x14,
        0x98, 0xC1, 0x00, 0x15,
        0x98, 0xC1, 0x00, 0x16,
        0x98, 0xE1, 0x00, 0x17,
        0x91, 0x21, 0x00, 0x18,
        0x38, 0x61, 0x00, 0x1C,
        0x3C, 0x80, message_receiver_string_ref[0], message_receiver_string_ref[1],
        0x60, 0x84, message_receiver_string_ref[2], message_receiver_string_ref[3],
        0x3D, 0x80, address_wstring_constructor[0], address_wstring_constructor[1],
        0x61, 0x8C, address_wstring_constructor[2], address_wstring_constructor[3],
        0x7D, 0x89, 0x03, 0xA6,
        0x4E, 0x80, 0x04, 0x21,
        0x38, 0x81, 0x00, 0x10,
        0x3D, 0x80, address_display_hud_memo[0], address_display_hud_memo[1],
        0x61, 0x8C, address_display_hud_memo[2], address_display_hud_memo[3],
        0x7D, 0x89, 0x03, 0xA6,
        0x4E, 0x80, 0x04, 0x21,
        0x80, 0x01, 0x00, 0x30,
        0x7C, 0x08, 0x03, 0xA6,
        0x38, 0x21, 0x00, 0x2C,
        0x4E, 0x80, 0x00, 0x20,
    ])

    dol_file.seek(patches["message_receiver_offset"])
    dol_file.write(message_receiver_patch)


def _apply_game_options_patch(binary_version: int, cosmetic_patches: CosmeticPatches, dol_file: BinaryIO):
    constructor_versions = {
        _GC_NTSC_DOL_VERSION: 0x15E95C,
    }
    game_options_offset = constructor_versions[binary_version]

    preferences = {
        "sound_mode": 1,
        "screen_brightness": 4,
        "screen_x_offset": 0,
        "screen_y_offset": 0,
        "screen_scretch": 0,
        "sfx_vol": 0x69,
        "music_vol": 0x4f,
        "hud_alpha": 0xff,
        "helmet_alpha": 0xff,
    }

    bitmask_flags = [False] * 8
    # 0: hud lag
    # 1: invert y-axis
    # 2: rumble
    # 3: crashes
    # 4: hint system
    # 5: doesn't crash, unknown
    # 6: doesn't crash, unknown
    # 7: doesn't crash, unknown
    bitmask_flags[0] = True
    bitmask = int("".join(str(int(flag)) for flag in bitmask_flags), 2)

    # Value ranges
    # screen_brightness: [0, 8]
    # screen_x_offset/screen_y_offset: [-0x1e, 0x1f]
    # screen_scretch: [-10, 10]
    # For sfx_vol/music_vol: [0x00, 0x69]

    # Patch stuff up
    # preferences["screen_brightness"] = 1
    # preferences["screen_x_offset"] = 12
    # preferences["screen_y_offset"] = 16
    # preferences["screen_scretch"] = 20
    # preferences["hud_alpha"] = 0xf0
    # preferences["helmet_alpha"] = 0x10

    patch = [
        # Unknown instructions, but keep for safety
        0x93, 0xe1, 0x00, 0x1c,  # *(r1 + 0x1c) = r31   (stw r31,0x1c(r1))

        0x7c, 0x7f, 0x1b, 0x78,  # r31 = r3 (ori r31,r3,r3)
        0x38, 0x61, 0x00, 0x08,  # r3 = r1 + 0x8 (addi r3,r1,0x8) For a later function call we don't touch
    ]
    for i, value in enumerate(preferences.values()):
        patch.extend([
            0x38, 0x00, 0x00, value,       # r0 = value (li r0, value)
            0x90, 0x1f, 0x00, (0x04 * i),  # *(r31 + offset) = r0  (stw r0,offset(r31))
        ])
    patch.extend([
        0x38, 0x00, 0x00, bitmask,
        # 0x90, 0x1f, 0x00, (0x04 * len(preferences)),
        0x98, 0x1f, 0x00, (0x04 * len(preferences)),
    ])

    # final_offset = 0x15E9E4
    # total_bytes_to_patch = final_offset - game_options_offset
    total_bytes_to_patch = 136
    bytes_to_fill = total_bytes_to_patch - len(patch)

    if bytes_to_fill < 0:
        raise RuntimeError(f"Our patch ({len(patch)}) is bigger than the space we have ({total_bytes_to_patch}).")

    if bytes_to_fill % 4 != 0:
        raise RuntimeError(f"The space left ({bytes_to_fill}) for is not a multiple of 4")

    patch.extend([0x60, 0x00, 0x00, 0x00] * (bytes_to_fill // 4))

    dol_file.seek(game_options_offset)
    dol_file.write(bytes(patch))


def apply_patches(game_root: Path, cosmetic_patches: CosmeticPatches):
    with game_root.joinpath("sys/main.dol").open("rb") as dol_file:
        dol_file.seek(0x1C)
        binary_version = int.from_bytes(dol_file.read(4), byteorder='big')

    with game_root.joinpath("sys/main.dol").open("r+b") as dol_file:
        _apply_string_display_patch(binary_version, dol_file)
        _apply_game_options_patch(binary_version, cosmetic_patches, dol_file)
