from __future__ import annotations

from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LayoutDamageStrictness(BitPackEnum, Enum):
    long_name: str

    STRICT = 1.0
    MEDIUM = 1.5
    LENIENT = 2.0


enum_lib.add_long_name(
    LayoutDamageStrictness,
    {
        LayoutDamageStrictness.STRICT: "Strict",
        LayoutDamageStrictness.MEDIUM: "Medium",
        LayoutDamageStrictness.LENIENT: "Lenient",
    },
)
