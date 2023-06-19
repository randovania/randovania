from randovania.games.game import RandovaniaGame
from randovania.games.prime2.patcher.echoes_dol_patches import BeamCostAddresses, IsDoorAddr, MapDoorTypeAddresses, SafeZoneAddresses, EchoesDolVersion, \
    StartingBeamVisorAddresses
from randovania.patching.prime.all_prime_dol_patches import StringDisplayPatchAddresses, HealthCapacityAddresses, \
    DangerousEnergyTankAddresses, PowerupFunctionsAddresses

ALL_VERSIONS = [
    EchoesDolVersion(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        description="Gamecube NTSC",
        build_string_address=0x803ac3b0,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32",
        sda2_base=0x804223c0,
        sda13_base=0x8041fd80,
        game_state_pointer=0x80418eb8,
        cplayer_vtable=0x803b15d0,
        cstate_manager_global=0x803db6e0,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038020,
            message_receiver_string_ref=0x803bd118,
            wstring_constructor=0x802ff3dc,
            display_hud_memo=0x8006b3c8,
            max_message_size=200,
        ),
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x800858f0,
            incr_pickup=0x80085760,
            decr_pickup=0x800856c4,
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
            is_out_of_ammo_to_shoot=0x801c92e8,
            gun_get_player=0x801dd758,
            get_item_amount=0x80085514,
        ),
        game_options_constructor_address=0x80161b48,
        safe_zone=SafeZoneAddresses(
            heal_per_frame_constant=0x8041a4fc,
            increment_health_fmr=0x8000c710,
        ),
        starting_beam_visor=StartingBeamVisorAddresses(
            player_state_constructor_clean=0x80086008,
            player_state_constructor_decode=0x80085c20,
            health_info_constructor=0x801420c8,
            enter_morph_ball_state=0x80184118,
            start_transition_to_visor=0x80085314,
            reset_visor=0x80085334,
        ),
        anything_set_address=0x8010f084,
        rs_debugger_printf_loop_address=0x8028c604,
        unvisited_room_names_address=0x8008b714,
        cworldtransmanager_sfxstart=0x80158e50,
        powerup_should_persist=0x803a743c,
        map_door_types=MapDoorTypeAddresses(
            get_correct_transform=IsDoorAddr(0x800bb4d8, 0x800bb4e0, 3),
            map_obj_draw=IsDoorAddr(0x800bb960, 0x800bb96c, 7),
            is_visible_to_automapper=IsDoorAddr(0x800bb600, 0x800bb608, 3),
            map_world_draw_areas=IsDoorAddr(0x8009458c, 0x80094594, 0),
            map_area_commit_resources1=IsDoorAddr(0x8007f3b4, 0x8007f3bc, 3),
            map_area_commit_resources2=IsDoorAddr(0x8007fab0, 0x8007fab8, 3),
            get_door_color=0x802175b4,
            map_icon_jumptable=0x803b3638,
        )
    ),
    EchoesDolVersion(
        game=RandovaniaGame.METROID_PRIME_ECHOES,
        description="Gamecube PAL",
        build_string_address=0x803ad710,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.035 10/27/2004 19:48:17",
        sda2_base=0x804236c0,
        sda13_base=0x80421060,
        game_state_pointer=0x8041A19C,
        cplayer_vtable=0x803b2950,
        cstate_manager_global=0x803dc900,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80038194,
            message_receiver_string_ref=0x803be378,
            wstring_constructor=0x802ff734,
            display_hud_memo=0x8006b504,
            max_message_size=200,
        ),
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x80085a2c,
            incr_pickup=0x8008589c,
            decr_pickup=0x80085800,
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
            is_out_of_ammo_to_shoot=0x801c961c,
            gun_get_player=0x801dda8c,
            get_item_amount=0x80085650,
        ),
        game_options_constructor_address=0x80161d9c,
        safe_zone=SafeZoneAddresses(
            heal_per_frame_constant=0x8041b7f4,
            increment_health_fmr=0x8000c754,
        ),
        starting_beam_visor=StartingBeamVisorAddresses(
            player_state_constructor_clean=0x80086144,
            player_state_constructor_decode=0x80085d5c,
            health_info_constructor=0x80142304,
            enter_morph_ball_state=0x801843f8,
            start_transition_to_visor=0x80085450,
            reset_visor=0x80085470,
        ),
        anything_set_address=0x8010f238,
        rs_debugger_printf_loop_address=0x8028ca0c,
        unvisited_room_names_address=0x8008b850,
        cworldtransmanager_sfxstart=0x801590a4,
        powerup_should_persist=0x803a7b94,
        map_door_types=None
    ),
]
