import dataclasses
import struct
from enum import Enum

from randovania.dol_patching.assembler.ppc import *
from randovania.dol_patching.dol_file import DolFile
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.games.prime.all_prime_dol_patches import BasePrimeDolVersion
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


@dataclasses.dataclass(frozen=True)
class BeamCostAddresses:
    uncharged_cost: int
    charged_cost: int
    charge_combo_ammo_cost: int
    charge_combo_missile_cost: int
    get_beam_ammo_type_and_costs: int


@dataclasses.dataclass(frozen=True)
class SafeZoneAddresses:
    heal_per_frame_constant: int
    increment_health_fmr: int


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


def apply_game_options_patch(game_options_constructor_offset: int, user_preferences: EchoesUserPreferences,
                             dol_file: DolFile):
    patch = [
        # Unknown purpose, but keep for safety
        *stw(r31, 0x1c, r1),
        *or_(r31, r3, r3),
        0x38, 0x61, 0x00, 0x08,  # r3 = r1 + 0x8 (addi r3,r1,0x8) For a later function call we don't touch
    ]

    for i, preference_name in enumerate(_PREFERENCES_ORDER):
        value = getattr(user_preferences, preference_name)
        if isinstance(value, Enum):
            value = value.value
        patch.extend([
            *li(r0, value),
            *stw(r0, (0x04 * i), r31),
        ])

    flag_values = [
        getattr(user_preferences, flag_name)
        if flag_name is not None else False
        for flag_name in _FLAGS_ORDER
    ]
    bit_mask = int("".join(str(int(flag)) for flag in flag_values), 2)
    patch.extend([
        *li(r0, bit_mask),
        *stb(r0, 0x04 * len(_PREFERENCES_ORDER), r31),
        *li(r0, 0),
        *stw(r0, 0x2c, r31),
        *stw(r0, 0x30, r31),
        *stw(r0, 0x34, r31),
    ])

    # final_offset = 0x15E9E4
    # total_bytes_to_patch = final_offset - game_options_offset
    total_bytes_to_patch = 136
    bytes_to_fill = total_bytes_to_patch - len(patch)

    if bytes_to_fill < 0:
        raise RuntimeError(f"Our patch ({len(patch)}) is bigger than the space we have ({total_bytes_to_patch}).")

    if bytes_to_fill % 4 != 0:
        raise RuntimeError(f"The space left ({bytes_to_fill}) for is not a multiple of 4")

    patch.extend(nop() * (bytes_to_fill // 4))
    dol_file.write(game_options_constructor_offset + 8 * 4, patch)


def apply_beam_cost_patch(patch_addresses: BeamCostAddresses, game_specific: EchoesGameSpecific,
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
        *li(r3, ammo_types[0][0]),
        *li(r9, ammo_types[0][1]),
        0x42, 0x80, 0x00, 0x2c,  # b update_out_beam_type

        # Dark Beam
        0x42, 0x00, 0x00, 0x10,  # bdnz dark_beam               # if (--count_register > 0) goto
        *li(r3, ammo_types[1][0]),
        *li(r9, ammo_types[1][1]),
        0x42, 0x80, 0x00, 0x1c,  # b update_out_beam_type

        # Light Beam
        0x42, 0x00, 0x00, 0x10,  # bdnz light_beam               # if (--count_register > 0) goto
        *li(r3, ammo_types[2][0]),
        *li(r9, ammo_types[2][1]),
        0x42, 0x80, 0x00, 0x0c,  # b update_out_beam_type

        # Annihilator Beam
        *li(r3, ammo_types[3][0]),
        *li(r9, ammo_types[3][1]),

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


def apply_safe_zone_heal_patch(patch_addresses: SafeZoneAddresses,
                               sda2_base: int,
                               game_specific: EchoesGameSpecific,
                               dol_file: DolFile):
    heal_per_second = game_specific.safe_zone_heal_per_second
    offset = patch_addresses.heal_per_frame_constant - sda2_base

    dol_file.write(patch_addresses.heal_per_frame_constant, struct.pack(">f", heal_per_second / 60))
    dol_file.write(patch_addresses.increment_health_fmr, lfs(f1, offset, r2))


@dataclasses.dataclass(frozen=True)
class EchoesDolVersion(BasePrimeDolVersion):
    beam_cost_addresses: BeamCostAddresses
    safe_zone: SafeZoneAddresses
