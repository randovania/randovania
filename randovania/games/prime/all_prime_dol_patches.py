import dataclasses
import struct
from typing import List

from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.dol_patching import assembler
from randovania.dol_patching.assembler import custom_ppc
from randovania.dol_patching.assembler.ppc import *
from randovania.dol_patching.dol_file import DolFile
from randovania.dol_patching.dol_version import DolVersion
from randovania.games.game import RandovaniaGame
from randovania.games.prime import prime_items


@dataclasses.dataclass(frozen=True)
class StringDisplayPatchAddresses(DataclassPostInitTypeCheck):
    update_hint_state: int
    message_receiver_string_ref: int
    wstring_constructor: int
    display_hud_memo: int
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
class PowerupFunctionsAddresses:
    """
    add_power_up: Change the given item capacity
    incr_pickup: Increments the given item amount
    decr_pickup: Decrements the given item amount
    """
    add_power_up: int
    incr_pickup: int
    decr_pickup: int


@dataclasses.dataclass(frozen=True)
class BasePrimeDolVersion(DolVersion):
    game_state_pointer: int
    cplayer_vtable: int
    cstate_manager_global: int
    string_display: StringDisplayPatchAddresses
    powerup_functions: PowerupFunctionsAddresses


_registers_to_save = 2
_remote_execution_stack_size = 0x30 + (_registers_to_save * 4)
_remote_execution_max_byte_count = 296


def remote_execution_patch_start() -> List[BaseInstruction]:
    return_code = remote_execution_patch_end()
    intro = [
        # setup stack
        stwu(r1, -(_remote_execution_stack_size - 4), r1),
        mfspr(r0, LR),
        stw(r0, _remote_execution_stack_size, r1),
        stmw(GeneralRegister(32 - _registers_to_save), _remote_execution_stack_size - 4 - _registers_to_save * 4, r1),
        or_(r31, r3, r3),

        # return if displayed
        lbz(r4, 0x2, r31),
        cmpwi(r4, 0x0),
        bne((len(return_code) + 1) * 4, relative=True),

        # clean return if flag is not set
        *return_code,

        # set displayed
        li(r6, 0x0),
        stb(r6, 0x2, r31),
    ]

    num_bytes_to_invalidate = _remote_execution_max_byte_count - assembler.byte_count(intro)
    # Our loop end condition depends on this value being a multiple of 32, greater than 0
    num_bytes_to_invalidate = ((num_bytes_to_invalidate // 32) + 1) * 32

    return [
        *intro,

        # fetch the instructions again, since they're being overwritten externally
        # this clears Dolphin's JIT cache
        custom_ppc.load_current_address(r30, 8),
        li(r4, num_bytes_to_invalidate),

        icbi(4, 30),  # invalidate using r30 + r4
        cmpwi(r4, 0x0),
        addi(r4, r4, -32),
        bne(-3 * 4, relative=True),
        sync(),
        isync(),
    ]


def remote_execution_patch_end() -> List[BaseInstruction]:
    return [
        lmw(GeneralRegister(32 - _registers_to_save), _remote_execution_stack_size - 4 - _registers_to_save * 4, r1),
        lwz(r0, _remote_execution_stack_size, r1),
        mtspr(LR, r0),
        addi(r1, r1, _remote_execution_stack_size - 4),
        blr(),
    ]


def call_display_hud_patch(patch_addresses: StringDisplayPatchAddresses) -> List[BaseInstruction]:
    # r31 = CStateManager
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
        custom_ppc.load_unsigned_32bit(r4, patch_addresses.message_receiver_string_ref),
        bl(patch_addresses.wstring_constructor),

        # r4 = CHUDMemoParms
        addi(r4, r1, 0x10),
        bl(patch_addresses.display_hud_memo),
    ]


def _load_player_state(game: RandovaniaGame, target_register: GeneralRegister, state_mgr: GeneralRegister = r31):
    if game == RandovaniaGame.METROID_PRIME:
        return [
            lwz(target_register, 0x8b8, state_mgr),
            lwz(target_register, 0, target_register),
        ]
    elif game == RandovaniaGame.METROID_PRIME_ECHOES:
        return [
            lwz(target_register, 0x150c, state_mgr),
        ]
    else:
        raise ValueError(f"Unsupported game {game}")


def adjust_item_amount_and_capacity_patch(
        patch_addresses: PowerupFunctionsAddresses, game: RandovaniaGame, item_id: int, delta: int,
) -> List[BaseInstruction]:
    # r31 = CStateManager
    if game == RandovaniaGame.METROID_PRIME and item_id in prime_items.ARTIFACT_ITEMS:
        return increment_item_capacity_patch(patch_addresses, game, item_id, delta)

    if delta >= 0:
        return [
            *increment_item_capacity_patch(patch_addresses, game, item_id, delta),
            *adjust_item_amount_patch(patch_addresses, game, item_id, delta),
        ]
    else:
        return [
            *adjust_item_amount_patch(patch_addresses, game, item_id, delta),
            *increment_item_capacity_patch(patch_addresses, game, item_id, delta),
        ]


def increment_item_capacity_patch(
        patch_addresses: PowerupFunctionsAddresses, game: RandovaniaGame, item_id: int, delta: int = 1,
) -> List[BaseInstruction]:
    return [
        *_load_player_state(game, r3, r31),
        li(r4, item_id),
        li(r5, delta),
        bl(patch_addresses.add_power_up),
    ]


def adjust_item_amount_patch(
        patch_addresses: PowerupFunctionsAddresses, game: RandovaniaGame, item_id: int, delta: int,
) -> List[BaseInstruction]:
    return [
        *_load_player_state(game, r3, r31),
        li(r4, item_id),
        li(r5, abs(delta)),
        bl(patch_addresses.incr_pickup if delta >= 0 else patch_addresses.decr_pickup),
    ]


def apply_remote_execution_patch(patch_addresses: StringDisplayPatchAddresses, dol_file: DolFile):
    patch = [
        *remote_execution_patch_start(),
        *remote_execution_patch_end(),
    ]
    dol_file.write_instructions(patch_addresses.update_hint_state, patch)


def create_remote_execution_body(patch_addresses: StringDisplayPatchAddresses,
                                 instructions: List[BaseInstruction]) -> Tuple[int, bytes]:
    """
    Return the address and the bytes for executing the given instructions via remote code execution.
    """
    update_hint_state = patch_addresses.update_hint_state

    remote_start_instructions = remote_execution_patch_start()
    remote_start_byte_count = assembler.byte_count(remote_start_instructions)

    body_address = update_hint_state + remote_start_byte_count
    body_instructions = list(instructions)
    body_instructions.extend(remote_execution_patch_end())
    body_bytes = bytes(assembler.assemble_instructions(body_address, body_instructions))

    if len(body_bytes) > _remote_execution_max_byte_count - remote_start_byte_count:
        raise ValueError(f"Received {len(body_instructions)} instructions with total {len(body_bytes)} bytes, "
                         f"but limit is {_remote_execution_max_byte_count - remote_start_byte_count}.")

    return body_address, body_bytes


def apply_energy_tank_capacity_patch(patch_addresses: HealthCapacityAddresses, energy_per_tank: int,
                                     dol_file: DolFile):
    """
    Patches the base health capacity and the energy tank capacity with matching values.
    """
    tank_capacity = float(energy_per_tank)

    dol_file.write(patch_addresses.base_health_capacity, struct.pack(">f", tank_capacity - 1))
    dol_file.write(patch_addresses.energy_tank_capacity, struct.pack(">f", tank_capacity))


def apply_reverse_energy_tank_heal_patch(sd2_base: int,
                                         addresses: DangerousEnergyTankAddresses,
                                         active: bool,
                                         game: RandovaniaGame,
                                         dol_file: DolFile,
                                         ):
    if game == RandovaniaGame.METROID_PRIME_ECHOES:
        health_offset = 0x14
        refill_item = 0x29
        patch_offset = 0x90

    elif game == RandovaniaGame.METROID_PRIME_CORRUPTION:
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
