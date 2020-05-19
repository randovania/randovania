import dataclasses
import struct
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Iterable

from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences

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
        struct_format = ">" + "L" * _NUM_SECTIONS
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


@dataclasses.dataclass(frozen=True)
class StringDisplayPatchAddresses:
    update_hint_state: int
    message_receiver_string_ref: int
    wstring_constructor: int
    display_hud_memo: int
    cstate_manager_global: int


@dataclasses.dataclass(frozen=True)
class PatchesForVersion:
    description: str
    build_string_address: int
    build_string: bytes
    string_display: StringDisplayPatchAddresses
    game_options_constructor_address: int


_ALL_VERSIONS_PATCHES = [
    PatchesForVersion(
        description="Gamecube NTSC",
        build_string_address=0x803ac3b0,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038020,
            message_receiver_string_ref=0x803a6380,
            wstring_constructor=0x802ff3dc,
            display_hud_memo=0x8006b3c8,
            cstate_manager_global=0x803db6e0,
        ),
        game_options_constructor_address=0x80161b48,
    ),
    PatchesForVersion(
        description="Gamecube PAL",
        build_string_address=0x803ad710,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.035 10/27/2004 19:48:17",
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038194,
            message_receiver_string_ref=0x803a680a,
            wstring_constructor=0x802ff734,
            display_hud_memo=0x8006b504,
            cstate_manager_global=0x803dc900,
        ),
        game_options_constructor_address=0x80161d9c,
    ),
]

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


def _apply_string_display_patch(patch_addresses: StringDisplayPatchAddresses, dol_file: DolFile):
    message_receiver_string_ref = struct.pack(">I", patch_addresses.message_receiver_string_ref)
    address_wstring_constructor = struct.pack(">I", patch_addresses.wstring_constructor)
    address_display_hud_memo = struct.pack(">I", patch_addresses.display_hud_memo)

    # setup stack
    # stwu r1,-0x2C(r1)
    # mfspr r0,LR
    # stw r0,0x30(r1)

    # # return if displayed
    # lbz r4,0x2(r3)
    # cmpwi r4,0x0
    # beq end

    # # otherwise set displayed
    # li r6,0x0
    # stb r6,0x2(r3)

    # # setup CHUDMemoParms
    # lis r5,0x4100 # 8.0f
    # li r7,0x1
    # li r9,0x9
    # stw r5,0x10(r1) # display time (seconds)
    # stb r7,0x14(r1) # clear memo window
    # stb r6,0x15(r1) # fade out only
    # stb r6,0x16(r1) # hint memo
    # stb r7,0x17(r1) # fade in text
    # stw r9,0x18(r1) # unk

    # # setup wstring
    # addi r3,r1,0x1C
    # lis r4,0x803a      # string pointer
    # ori r4,r4,0x6380
    # lis r12,0x802f     # wstring_l constructor
    # ori r12,r12,0xf3dc
    # mtspr CTR,r12
    # bctrl # rstl::wstring_l

    # # r3 = wstring
    # addi r4,r1,0x10
    # lis r12,0x8006     # DisplayHudMemo address
    # ori r12,r12,0xb3c8
    # mtspr CTR,r12
    # bctrl # CSamusHud::DisplayHudMemo

    # end:
    # lwz r0,0x30(r1)
    # mtspr LR,r0
    # addi r1,r1,0x2C
    # blr

    message_receiver_patch = [
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
    ]

    dol_file.write(patch_addresses.update_hint_state, message_receiver_patch)


def _apply_game_options_patch(game_options_constructor_offset: int, user_preferences: EchoesUserPreferences,
                              dol_file: DolFile):
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
    dol_file.write(game_options_constructor_offset + 8 * 4, patch)


def apply_patches(game_root: Path, cosmetic_patches: CosmeticPatches):
    dol_file = DolFile(_get_dol_path(game_root))

    version_patches = _read_binary_version(dol_file)

    dol_file.set_editable(True)
    with dol_file:
        _apply_string_display_patch(version_patches.string_display, dol_file)
        _apply_game_options_patch(version_patches.game_options_constructor_address,
                                  cosmetic_patches.user_preferences, dol_file)


def _get_dol_path(game_root: Path) -> Path:
    return game_root.joinpath("sys/main.dol")


def _read_binary_version(dol_file: DolFile) -> PatchesForVersion:
    dol_file.set_editable(False)
    with dol_file:
        for version in _ALL_VERSIONS_PATCHES:
            build_string = dol_file.read(version.build_string_address, len(version.build_string))
            if build_string == version.build_string:
                return version

    raise RuntimeError(f"Unsupported game version")
