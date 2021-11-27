from randovania.games.prime1.patcher.prime1_dol_patches import Prime1DolVersion

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
    Prime1DolVersion(
        version="0-02",
        description="GC NTSC 0-02",
        build_string_address=0x803cd648,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.111 3/10/2003 17:56:21",
        sda2_base=0x805b2de0,
        sda13_base=0x805afc40,
        cplayer_vtable=0x803da7a8,
        message_receiver_string_ref=0x803f0ba8,
    ),
    Prime1DolVersion(
        version="pal",
        description="GC PAL",
        build_string_address=0x803b6924,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.110 2/4/2003 22:16:07",
        sda2_base=0x80473e60,
        sda13_base=0x80470c60,
        cplayer_vtable=0x803c4b88,
        message_receiver_string_ref=0x803d7a28,
    ),
    Prime1DolVersion(
        version="kor",
        description="GC NTSC-K",
        build_string_address=0x803cc688,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.097 12/19/2002 16:03:43",
        sda2_base=0x805b1a00,
        sda13_base=0x805ae8a0,
        cplayer_vtable=0x803d97e8,
        message_receiver_string_ref=0x803efc90,
    ),
    Prime1DolVersion(
        version="jap",
        description="GC NTSC-J",
        build_string_address=0x803b86cc,
        build_string=b"!#$MetroidBuildInfo!#$Build v1.111 2/11/2003 10:03:22",
        sda2_base=0x8059ae00,
        sda13_base=0x80597c20,
        cplayer_vtable=0x803c5b28,
        message_receiver_string_ref=0x803d89c8,
    ),
]
