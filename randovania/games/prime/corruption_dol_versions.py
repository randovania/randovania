from randovania.games.game import RandovaniaGame
from randovania.games.prime.all_prime_dol_patches import StringDisplayPatchAddresses, HealthCapacityAddresses, \
    DangerousEnergyTankAddresses
from randovania.games.prime.corruption_dol_patches import CorruptionDolVersion
from randovania.games.prime.echoes_dol_patches import BeamCostAddresses, SafeZoneAddresses, EchoesDolVersion

ALL_VERSIONS = [
    CorruptionDolVersion(
        game=RandovaniaGame.PRIME3,
        description="Wii NTSC",
        build_string_address=0x805822b0,
        build_string=b"!#$MetroidBuildInfo!#$2007/07/27 13:13 Build v3.436 (MP3)",
        sda2_base=0x806869C0,
        game_state_pointer=None,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=None,
            message_receiver_string_ref=0x805a4200,
            wstring_constructor=None,
            display_hud_memo=None,
            cstate_manager_global=0x8067dc0c,
            max_message_size=200,
        ),
        health_capacity=HealthCapacityAddresses(
            base_health_capacity=0x80680a6c,
            energy_tank_capacity=0x80680a70,
        ),
        dangerous_energy_tank=DangerousEnergyTankAddresses(
            small_number_float=0x8067fe8c,
            incr_pickup=0x801913a0,
        ),
        game_options_constructor_address=None,
    ),
]
