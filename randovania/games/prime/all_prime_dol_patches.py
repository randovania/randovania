import dataclasses
import struct
from typing import List, Tuple

from randovania.dol_patching import assembler
from randovania.dol_patching.assembler import custom_ppc
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


def remote_execution_patch_start(start_address: int):
    return_code = remote_execution_patch_end()
    patch_intro = [
        # setup stack
        stwu(r1, -0x2C, r1),
        mfspr(r0, LR),
        stw(r0, 0x30, r1),

        # return if displayed
        lbz(r4, 0x2, r3),
        cmpwi(r4, 0x0),
        bne((len(return_code) + 1) * 4, relative=True),

        # clean return if flag is not set
        *return_code,

        # set displayed
        li(r6, 0x0),
        stb(r6, 0x2, r3),
    ]
    patch_sync = [
        sync(),
        icbi(0, 4),
        isync(),
    ]

    patch = [
        *patch_intro,
        *custom_ppc.load_unsigned_32bit(r4, 0),
        *patch_sync,
    ]
    return [
        *patch_intro,
        *custom_ppc.load_unsigned_32bit(r4, start_address + len(patch) * 4),
        *patch_sync,
    ]


def remote_execution_patch_end():
    return [
        lwz(r0, 0x30, r1),
        mtspr(LR, r0),
        addi(r1, r1, 0x2C),
        blr(),
    ]


def call_display_hud_patch(patch_addresses: StringDisplayPatchAddresses):
    return [
        # setup CHUDMemoParms
        lis(r5, 0x4100),  # 8.0f
        li(r6, 0x0),
        li(r7, 0x1),
        li(r9, 0x9),
        stw(r5, 0x10, r1),  # display time (seconds)
        stb(r7, 0x14, r1),  # clear memo window
        stb(r6, 0x15, r1),  # fade out only
        stb(r6, 0x16, r1),  # hint memo
        stb(r7, 0x17, r1),  # fade in text
        stw(r9, 0x18, r1),  # unk

        # setup wstring
        addi(r3, r1, 0x1C),
        *custom_ppc.load_unsigned_32bit(r4, patch_addresses.message_receiver_string_ref),
        bl(patch_addresses.wstring_constructor),

        # r4 = CHUDMemoParms
        addi(r4, r1, 0x10),
        bl(patch_addresses.display_hud_memo),
    ]


def give_item_patch(patch_addresses: StringDisplayPatchAddresses, item_id: int, quantity: int):
    add_power_up = 0x800858f0
    incr_pickup = 0x80085760
    return [
        *custom_ppc.load_unsigned_32bit(r3, patch_addresses.cstate_manager_global),
        lwz(r3, 0x150c, r3),
        li(r4, item_id),
        li(r5, quantity),
        bl(add_power_up),

        *custom_ppc.load_unsigned_32bit(r3, patch_addresses.cstate_manager_global),
        lwz(r3, 0x150c, r3),
        li(r4, item_id),
        li(r5, quantity),
        bl(incr_pickup),
    ]


def apply_remote_execution_patch(patch_addresses: StringDisplayPatchAddresses, dol_file: DolFile):
    patch = [
        *remote_execution_patch_start(patch_addresses.update_hint_state),
        *remote_execution_patch_end(),
    ]
    dol_file.write_instructions(patch_addresses.update_hint_state, patch)


def create_remote_execution_body(patch_addresses: StringDisplayPatchAddresses,
                                 instructions: List[Instruction]) -> Tuple[int, bytes]:
    """
    Return the address and the bytes for executing the given instructions via remote code execution.
    """
    update_hint_state = patch_addresses.update_hint_state
    max_instruction_count = 74

    remote_start_instructions = remote_execution_patch_start(update_hint_state)
    body_instructions = [*instructions, *remote_execution_patch_end()]

    if len(body_instructions) > max_instruction_count - len(remote_start_instructions):
        raise ValueError(f"Received {len(body_instructions)} instructions, "
                         f"but limit is {max_instruction_count - len(remote_start_instructions)}.")

    patch_address = update_hint_state + len(remote_start_instructions) * 4
    patch_bytes = bytes(assembler.assemble_instructions(patch_address, body_instructions))
    return patch_address, patch_bytes


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
