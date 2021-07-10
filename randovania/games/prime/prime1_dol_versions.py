from randovania.games.game import RandovaniaGame
from randovania.games.prime.all_prime_dol_patches import StringDisplayPatchAddresses, PowerupFunctionsAddresses
from randovania.games.prime.prime1_dol_patches import Prime1DolVersion

ALL_VERSIONS = [
    Prime1DolVersion(
        game=RandovaniaGame.METROID_PRIME,
        description="GC NTSC 0-00",
        build_string_address=0x803cc588,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.088 10/29/2002 2:21:25",
        sda2_base=0x805b1d20,
        game_state_pointer=0x805a8c40,
        cplayer_vtable=0x803d96e8,
        cstate_manager_global=0x8045a1a8,
        string_display=StringDisplayPatchAddresses(
            update_hint_state=0x80044d38,
            message_receiver_string_ref=0x803efb90,
            wstring_constructor=0x800159f0,
            display_hud_memo=0x8006bc68,
            max_message_size=200,
        ),
        powerup_functions=PowerupFunctionsAddresses(
            add_power_up=0x80091d68,
            incr_pickup=0x80091bf0,
            decr_pickup=0x80091b94,
        ),
    ),
]
