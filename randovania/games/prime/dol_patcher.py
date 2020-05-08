import dataclasses
import struct
from enum import Enum
from pathlib import Path
from typing import BinaryIO

from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences

_GC_NTSC_DOL_VERSION = 0x003A22A0
_GC_PAL_DOL_VERSION = None


@dataclasses.dataclass(frozen=True)
class StringDisplayPatchOffsets:
    message_receiver_file_offset: int
    message_receiver_string_ref: int
    wstring_constructor: int
    display_hud_memo: int


@dataclasses.dataclass(frozen=True)
class PatchesForVersion:
    string_display: StringDisplayPatchOffsets
    game_options_file_offset: int


_ALL_VERSIONS_PATCHES = {
    _GC_NTSC_DOL_VERSION: PatchesForVersion(
        string_display=StringDisplayPatchOffsets(
            message_receiver_file_offset=0x34E20,
            message_receiver_string_ref=0x803a6380,
            wstring_constructor=0x802ff3dc,
            display_hud_memo=0x8006b3c8,
        ),
        game_options_file_offset=0x15E95C,
    ),
    _GC_PAL_DOL_VERSION: PatchesForVersion(
        string_display=StringDisplayPatchOffsets(
            message_receiver_file_offset=0x15EB9C,
            message_receiver_string_ref=0x803a680a,
            wstring_constructor=0x802ff734,
            display_hud_memo=0x8006b504,
        ),
        game_options_file_offset=0x15EBB0,
    ),
}

_PREFERENCES_ORDER = (
    "sound_mode",
    "screen_brightness",
    "screen_x_offset",
    "screen_y_offset",
    "screen_stretch",
    "sfx_volume",
    "music_volume",
    "hud_alpha",
    "helmet_alpha",
)
_FLAGS_ORDER = (
    "hud_lag",
    "invert_y_axis",
    "rumble",
    None,  # crashes, maybe swapBeamsControls
    "hint_system",
    None,  # 5: doesn't crash, unknown
    None,  # 6: doesn't crash, unknown
    None,  # 7: doesn't crash, unknown
)


def _apply_string_display_patch(patch_offsets: StringDisplayPatchOffsets, dol_file: BinaryIO):
    message_receiver_string_ref = struct.pack(">I", patch_offsets.message_receiver_string_ref)
    address_wstring_constructor = struct.pack(">I", patch_offsets.wstring_constructor)
    address_display_hud_memo = struct.pack(">I", patch_offsets.display_hud_memo)

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

    dol_file.seek(patch_offsets.message_receiver_file_offset)
    dol_file.write(message_receiver_patch)


def _apply_game_options_patch(game_options_file_offset: int, user_preferences: EchoesUserPreferences,
                              dol_file: BinaryIO):
    patch = [
        # Unknown purpose, but keep for safety
        0x93, 0xe1, 0x00, 0x1c,  # *(r1 + 0x1c) = r31   (stw r31,0x1c(r1))

        0x7c, 0x7f, 0x1b, 0x78,  # r31 = r3 (ori r31,r3,r3)
        0x38, 0x61, 0x00, 0x08,  # r3 = r1 + 0x8 (addi r3,r1,0x8) For a later function call we don't touch
    ]

    for i, preference_name in enumerate(_PREFERENCES_ORDER):
        value = getattr(user_preferences, preference_name)
        if isinstance(value, Enum):
            value = value.value
        encoded_value = struct.pack(">h", value)
        patch.extend([
            0x38, 0x00, encoded_value[0], encoded_value[1],  # r0 = value (li r0, value)
            0x90, 0x1f, 0x00, (0x04 * i),  # *(r31 + offset) = r0  (stw r0,offset(r31))
        ])

    flag_values = [
        getattr(user_preferences, flag_name)
        if flag_name is not None else False
        for flag_name in _FLAGS_ORDER
    ]
    bit_mask = int("".join(str(int(flag)) for flag in flag_values), 2)
    patch.extend([
        0x38, 0x00, 0x00, bit_mask,
        # 0x90, 0x1f, 0x00, (0x04 * len(_PREFERENCES_ORDER)),
        0x98, 0x1f, 0x00, (0x04 * len(_PREFERENCES_ORDER)),
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

    dol_file.seek(game_options_file_offset)
    dol_file.write(bytes(patch))


def apply_patches(game_root: Path, cosmetic_patches: CosmeticPatches):
    binary_version = _read_binary_version(game_root)
    try:
        version_patches = _ALL_VERSIONS_PATCHES[binary_version]
    except KeyError:
        raise RuntimeError(f"Unsupported game version")

    with _get_dol_path(game_root).open("r+b") as dol_file:
        _apply_string_display_patch(version_patches.string_display, dol_file)
        _apply_game_options_patch(version_patches.game_options_file_offset,
                                  cosmetic_patches.user_preferences, dol_file)


def _get_dol_path(game_root: Path) -> Path:
    return game_root.joinpath("sys/main.dol")


def _read_binary_version(game_root: Path) -> int:
    with _get_dol_path(game_root).open("rb") as dol_file:
        dol_file.seek(0x1C)
        return int.from_bytes(dol_file.read(4), byteorder='big')
