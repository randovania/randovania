from randovania.games.prime.prime1_dol_patches import Prime1DolVersion

ALL_VERSIONS = [
    Prime1DolVersion(
        version="0-00",
        description="GC NTSC 0-00",
        build_string_address=0x803cc588,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.088 10/29/2002 2:21:25",
        sda2_base=0x805b1d20,
        sda13_base=0x805aebc0,
        cplayer_vtable=0x803d96e8,
        message_receiver_string_ref=0x803efb90,
    ),
]
