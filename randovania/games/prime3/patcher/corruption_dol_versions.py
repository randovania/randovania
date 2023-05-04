from randovania.games.game import RandovaniaGame
from randovania.games.prime3.patcher.corruption_dol_patches import CorruptionDolVersion
from randovania.patching.prime.all_prime_dol_patches import PowerupFunctionsAddresses

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
    CorruptionDolVersion(
        game=RandovaniaGame.METROID_PRIME_CORRUPTION,
        description="Wii PAL",
        build_string_address=0x805843a8,
        build_string=b"!#$MetroidBuildInfo!#$2007/08/24 16:52 Build v3.453 (mp3)",
        sda2_base=0x80688fe0,
        sda13_base=0x806827c0,
        game_state_pointer=0x80680234,
        cplayer_vtable=0x80595238,
        cstate_manager_global=0x805c7570,

        string_display=None,
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x80191e2c,
            incr_pickup=0x801920b0,
            decr_pickup=0x8019222c,
        ),
    ),
    CorruptionDolVersion(
        game=RandovaniaGame.METROID_PRIME_CORRUPTION,
        description="Wii NTSC-J",
        build_string_address=0x80587c2c,
        build_string=b"!#$MetroidBuildInfo!#$2007/11/12 14:15 Build v3.495 (jpn)",
        sda2_base=0x8068c840,
        sda13_base=0x80686000,
        game_state_pointer=0x80683a7c,
        cplayer_vtable=0x80598650,
        cstate_manager_global=0x805caa30,

        string_display=None,
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x801932d0,
            incr_pickup=0x80193554,
            decr_pickup=0x801936d0,
        ),
    ),
]
