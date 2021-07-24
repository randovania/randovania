from randovania.games.game import RandovaniaGame
from randovania.games.prime.all_prime_dol_patches import StringDisplayPatchAddresses, PowerupFunctionsAddresses
from randovania.games.prime.corruption_dol_patches import CorruptionDolVersion

ALL_VERSIONS = [
    CorruptionDolVersion(
        game=RandovaniaGame.METROID_PRIME_CORRUPTION,
        description="Wii NTSC",
        build_string_address=0x805822b0,
        build_string=b"!#$MetroidBuildInfo!#$2007/07/27 13:13 Build v3.436 (MP3)",
        sda2_base=0x806869C0,
        sda13_base=0x806801c0,
        game_state_pointer=0x8067dc0c,
        cplayer_vtable=0x80592c78,
        cstate_manager_global=0x805c4f70,

        string_display=None,
        # string_display=StringDisplayPatchAddresses(
        #     update_hint_state=None,
        #     message_receiver_string_ref=0x805a4200,
        #     wstring_constructor=None,
        #     display_hud_memo=0x801c6480,
        #     max_message_size=200,
        # ),
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x8019111c,
            incr_pickup=0x801913a0,
            decr_pickup=0x8019151c,
        ),
    ),
]
