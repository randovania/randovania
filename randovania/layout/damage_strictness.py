from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutDamageStrictness(BitPackEnum, Enum):
    STRICT = 1.0
    MEDIUM = 1.5
    LENIENT = 2.0

    @classmethod
    def default(cls):
        return cls.MEDIUM

    @property
    def long_name(self) -> str:
        if self == LayoutDamageStrictness.STRICT:
            return "Strict"
        elif self == LayoutDamageStrictness.MEDIUM:
            return "Medium"
        elif self == LayoutDamageStrictness.LENIENT:
            return "Lenient"
        else:
            return "Custom"
