import dataclasses
import struct

from randovania.dol_patching.assembler.ppc import *
from randovania.dol_patching.dol_file import DolFile
from randovania.dol_patching.dol_version import DolVersion
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.games.game import RandovaniaGame


@dataclasses.dataclass(frozen=True)
class StringDisplayPatchAddresses:
    update_hint_state: int
    message_receiver_string_ref: int
    wstring_constructor: int
    display_hud_memo: int
    cstate_manager_global: int
    max_message_size: int


@dataclasses.dataclass(frozen=True)
class HealthCapacityAddresses:
    base_health_capacity: int
    energy_tank_capacity: int


@dataclasses.dataclass(frozen=True)
class DangerousEnergyTankAddresses:
    small_number_float: int
    incr_pickup: int


@dataclasses.dataclass(frozen=True)
class BasePrimeDolVersion(DolVersion):
    game_state_pointer: int
    string_display: StringDisplayPatchAddresses
    health_capacity: HealthCapacityAddresses
    game_options_constructor_address: int
    dangerous_energy_tank: DangerousEnergyTankAddresses


def apply_string_display_patch(patch_addresses: StringDisplayPatchAddresses, dol_file: DolFile):
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


def apply_energy_tank_capacity_patch(patch_addresses: HealthCapacityAddresses, game_specific: EchoesGameSpecific,
                                     dol_file: DolFile):
    """
    Patches the base health capacity and the energy tank capacity with matching values.
    """
    tank_capacity = game_specific.energy_per_tank

    dol_file.write(patch_addresses.base_health_capacity, struct.pack(">f", tank_capacity - 1))
    dol_file.write(patch_addresses.energy_tank_capacity, struct.pack(">f", tank_capacity))


def apply_reverse_energy_tank_heal_patch(sd2_base: int,
                                         addresses: DangerousEnergyTankAddresses,
                                         active: bool,
                                         game: RandovaniaGame,
                                         dol_file: DolFile,
                                         ):
    if game == RandovaniaGame.PRIME2:
        health_offset = 0x14
        refill_item = 0x29
        patch_offset = 0x90

    elif game == RandovaniaGame.PRIME3:
        health_offset = 0xc
        refill_item = 0x12
        patch_offset = 0x138

    else:
        raise ValueError(f"Unsupported game: {game}")

    if active:
        patch = [
            lfs(f0, (addresses.small_number_float - sd2_base), r2),
            stfs(f0, health_offset, r30),
            ori(r0, r0, 0),
            ori(r0, r0, 0),
        ]
    else:
        patch = [
            or_(r3, r30, r30),
            li(r4, refill_item),
            li(r5, 9999),
            bl(addresses.incr_pickup),
        ]

    dol_file.write_instructions(addresses.incr_pickup + patch_offset, patch)
