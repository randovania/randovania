from randovania.games.game import RandovaniaGame
from randovania.games.prime.all_prime_dol_patches import StringDisplayPatchAddresses, HealthCapacityAddresses, \
    DangerousEnergyTankAddresses
from randovania.games.prime.echoes_dol_patches import BeamCostAddresses, SafeZoneAddresses, EchoesDolVersion

ALL_VERSIONS = [
    EchoesDolVersion(
        game=RandovaniaGame.PRIME2,
        description="Gamecube NTSC",
        build_string_address=0x803ac3b0,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
        sda2_base=0x804223c0,
        game_state_pointer=0x80418eb8,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038020,
            message_receiver_string_ref=0x803bd118,
            wstring_constructor=0x802ff3dc,
            display_hud_memo=0x8006b3c8,
            cstate_manager_global=0x803db6e0,
            max_message_size=200,
        ),
        health_capacity=HealthCapacityAddresses(
            base_health_capacity=0x8041abe4,
            energy_tank_capacity=0x8041abe0,
        ),
        dangerous_energy_tank=DangerousEnergyTankAddresses(
            small_number_float=0x8041a4a8,
            incr_pickup=0x80085760,
        ),
        beam_cost_addresses=BeamCostAddresses(
            uncharged_cost=0x803aa8c8,
            charged_cost=0x803aa8d8,
            charge_combo_ammo_cost=0x803aa8e8,
            charge_combo_missile_cost=0x803a74ac,
            get_beam_ammo_type_and_costs=0x801cccb0,
        ),
        game_options_constructor_address=0x80161b48,
        safe_zone=SafeZoneAddresses(
            heal_per_frame_constant=0x8041a4fc,
            increment_health_fmr=0x8000c710,
        ),
    ),
    EchoesDolVersion(
        game=RandovaniaGame.PRIME2,
        description="Gamecube PAL",
        build_string_address=0x803ad710,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.035 10/27/2004 19:48:17",
        sda2_base=0x804223c0,
        game_state_pointer=0x8041A19C,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038194,
            message_receiver_string_ref=0x803be378,
            wstring_constructor=0x802ff734,
            display_hud_memo=0x8006b504,
            cstate_manager_global=0x803dc900,
            max_message_size=200,
        ),
        health_capacity=HealthCapacityAddresses(
            base_health_capacity=0x8041bedc,
            energy_tank_capacity=0x8041bed8,
        ),
        dangerous_energy_tank=DangerousEnergyTankAddresses(
            small_number_float=0x8041b7a0,
            incr_pickup=0x8008589c,
        ),
        beam_cost_addresses=BeamCostAddresses(
            uncharged_cost=0x803abc28,
            charged_cost=0x803abc38,
            charge_combo_ammo_cost=0x803abc48,
            charge_combo_missile_cost=0x803a7c04,
            get_beam_ammo_type_and_costs=0x801ccfe4,
        ),
        game_options_constructor_address=0x80161d9c,
        safe_zone=SafeZoneAddresses(
            heal_per_frame_constant=0x8041b7f4,
            increment_health_fmr=0x8000c754,
        ),
    ),
]
