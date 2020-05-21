import dataclasses
import struct
from enum import Enum
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Iterable

from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.game_description.game_patches import GamePatches
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


@dataclasses.dataclass(frozen=True)
class StringDisplayPatchAddresses:
    update_hint_state: int
    message_receiver_string_ref: int
    wstring_constructor: int
    display_hud_memo: int
    cstate_manager_global: int


@dataclasses.dataclass(frozen=True)
class HealthCapacityAddresses:
    base_health_capacity: int
    energy_tank_capacity: int


@dataclasses.dataclass(frozen=True)
class BeamCostAddresses:
    uncharged_cost: int
    charged_cost: int
    charge_combo_ammo_cost: int
    charge_combo_missile_cost: int
    get_beam_ammo_type_and_costs: int


@dataclasses.dataclass(frozen=True)
class PatchesForVersion:
    description: str
    build_string_address: int
    build_string: bytes
    string_display: StringDisplayPatchAddresses
    health_capacity: HealthCapacityAddresses
    beam_cost_addresses: BeamCostAddresses
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
        health_capacity=HealthCapacityAddresses(
            base_health_capacity=0x8041abe4,
            energy_tank_capacity=0x8041abe0,
        ),
        beam_cost_addresses=BeamCostAddresses(
            uncharged_cost=0x803aa8c8,
            charged_cost=0x803aa8d8,
            charge_combo_ammo_cost=0x803aa8e8,
            charge_combo_missile_cost=0x803a74ac,
            get_beam_ammo_type_and_costs=0x801cccb0,
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
        health_capacity=HealthCapacityAddresses(
            base_health_capacity=0x8041bedc,
            energy_tank_capacity=0x8041bed8,
        ),
        beam_cost_addresses=BeamCostAddresses(
            uncharged_cost=0x803abc28,
            charged_cost=0x803abc38,
            charge_combo_ammo_cost=0x803abc48,
            charge_combo_missile_cost=0x803a7c04,
            get_beam_ammo_type_and_costs=0x801ccfe4,
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
        0x98, 0x1f, 0x00, (0x04 * len(_PREFERENCES_ORDER)),
    ])
    patch.extend([
        0x38, 0x00, 0x00, 0x00,  # li r0, value)
        0x90, 0x1f, 0x00, 0x2c,  # stw r0 ,0x2c (r31)
        0x90, 0x1f, 0x00, 0x30,  # stw r0 ,0x30 (r31)
        0x90, 0x1f, 0x00, 0x34,  # stw r0 ,0x34 (r31)
    ])

    # final_offset = 0x15E9E4
    # total_bytes_to_patch = final_offset - game_options_offset
    total_bytes_to_patch = 136
    bytes_to_fill = total_bytes_to_patch - len(patch)

    if bytes_to_fill < 0:
        raise RuntimeError(f"Our patch ({len(patch)}) is bigger than the space we have ({total_bytes_to_patch}).")

    if bytes_to_fill % 4 != 0:
        raise RuntimeError(f"The space left ({bytes_to_fill}) for is not a multiple of 4")

    # ori r0, r0, 0x0 is a no-op
    patch.extend([0x60, 0x00, 0x00, 0x00] * (bytes_to_fill // 4))
    dol_file.write(game_options_constructor_offset + 8 * 4, patch)


def _apply_energy_tank_capacity_patch(patch_addresses: HealthCapacityAddresses, game_specific: EchoesGameSpecific,
                                      dol_file: DolFile):
    """
    Patches the base health capacity and the energy tank capacity with matching values.
    """
    tank_capacity = game_specific.energy_per_tank

    dol_file.write(patch_addresses.base_health_capacity, struct.pack(">f", tank_capacity - 1))
    dol_file.write(patch_addresses.energy_tank_capacity, struct.pack(">f", tank_capacity))


def _apply_beam_cost_patch(patch_addresses: BeamCostAddresses, game_specific: EchoesGameSpecific,
                           dol_file: DolFile):
    uncharged_costs = []
    charged_costs = []
    combo_costs = []
    missile_costs = []
    ammo_types = []

    for beam_config in game_specific.beam_configurations:
        uncharged_costs.append(beam_config.uncharged_cost)
        charged_costs.append(beam_config.charged_cost)
        combo_costs.append(beam_config.combo_ammo_cost)
        missile_costs.append(beam_config.combo_missile_cost)
        ammo_types.append((
            beam_config.ammo_a.index if beam_config.ammo_a is not None else -1,
            beam_config.ammo_b.index if beam_config.ammo_b is not None else -1,
        ))

    uncharged_costs_patch = struct.pack(">llll", *uncharged_costs)
    charged_costs_patch = struct.pack(">llll", *charged_costs)
    combo_costs_patch = struct.pack(">llll", *combo_costs)
    missile_costs_patch = struct.pack(">llll", *missile_costs)

    def enc(i, x):
        return struct.pack(">h", ammo_types[i][x])

    # TODO: patch CPlayerGun::IsOutOfAmmoToShoot

    # The following patch also changes the fact that the game doesn't check if there's enough ammo for Power Beam
    # we start our patch right after the `addi r3,r31,0x0`
    ammo_type_patch_offset = 0x40
    ammo_type_patch = [
        0x81, 0x59, 0x07, 0x74,  # lwz r10,0x774(r25)           # r10 = get current beam
        0x55, 0x4a, 0x10, 0x3a,  # rlwinm r10,r10,0x2,0x0,0x1d  # r10 *= 4

        0x7c, 0x03, 0x50, 0x2e,  # lwzx r0,r3,r10               # r0 = BeamIdToUnchargedShotAmmoCost[currentBeam]
        0x90, 0x1d, 0x00, 0x00,  # stw r0,0x0(r29)              # *outBeamAmmoCost = r0

        0x81, 0x59, 0x07, 0x74,  # lwz r10,0x774(r25)           # r10 = get current beam
        0x39, 0x4a, 0x00, 0x01,  # addi r10,r10,0x1             # r10 = r10
        0x7d, 0x49, 0x03, 0xa6,  # mtspr CTR,r10                # count_register = r10

        # Power Beam
        0x42, 0x00, 0x00, 0x10,  # bdnz dark_beam               # if (--count_register > 0) goto
        0x38, 0x60, *enc(0, 0),  # li r3, <type>
        0x39, 0x20, *enc(0, 1),  # li r9, <type>
        0x42, 0x80, 0x00, 0x2c,  # b update_out_beam_type

        # Dark Beam
        0x42, 0x00, 0x00, 0x10,  # bdnz dark_beam               # if (--count_register > 0) goto
        0x38, 0x60, *enc(1, 0),  # li r3, <type>
        0x39, 0x20, *enc(1, 1),  # li r9, <type>
        0x42, 0x80, 0x00, 0x1c,  # b update_out_beam_type

        # Light Beam
        0x42, 0x00, 0x00, 0x10,  # bdnz light_beam               # if (--count_register > 0) goto
        0x38, 0x60, *enc(2, 0),  # li r3, <type>
        0x39, 0x20, *enc(2, 1),  # li r9, <type>
        0x42, 0x80, 0x00, 0x0c,  # b update_out_beam_type

        # Annihilator Beam
        0x38, 0x60, *enc(3, 0),  # li r3, <type>
        0x39, 0x20, *enc(3, 1),  # li r9, <type>

        # update_out_beam_type
        0x90, 0x7b, 0x00, 0x00,  # stw r0,0x0(r27)              # *outBeamAmmoTypeA = r3
        0x91, 0x3c, 0x00, 0x00,  # stw r0,0x0(r28)              # *outBeamAmmoTypeB = r8

        0x42, 0x80, 0x00, 0x18,  # b body_end
        # jump to the code for getting the charged/combo costs and then check if has ammo
        # The address in question is at 0x801ccd64 for NTSC
    ]

    dol_file.write(patch_addresses.uncharged_cost, uncharged_costs_patch)
    dol_file.write(patch_addresses.charged_cost, charged_costs_patch)
    dol_file.write(patch_addresses.charge_combo_ammo_cost, combo_costs_patch)
    dol_file.write(patch_addresses.charge_combo_missile_cost, missile_costs_patch)
    dol_file.write(patch_addresses.get_beam_ammo_type_and_costs + ammo_type_patch_offset, ammo_type_patch)


def apply_patches(game_root: Path, game_patches: GamePatches, cosmetic_patches: CosmeticPatches):
    dol_file = DolFile(_get_dol_path(game_root))

    version_patches = _read_binary_version(dol_file)

    dol_file.set_editable(True)
    with dol_file:
        _apply_string_display_patch(version_patches.string_display, dol_file)
        _apply_game_options_patch(version_patches.game_options_constructor_address,
                                  cosmetic_patches.user_preferences, dol_file)
        _apply_energy_tank_capacity_patch(version_patches.health_capacity, game_patches.game_specific, dol_file)
        _apply_beam_cost_patch(version_patches.beam_cost_addresses, game_patches.game_specific, dol_file)


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
