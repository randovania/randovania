from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutElevators(BitPackEnum, Enum):
    VANILLA = "vanilla"
    TWO_WAY_RANDOMIZED = "randomized"
    TWO_WAY_UNCHECKED = "two-way-unchecked"
    ONE_WAY_ELEVATOR = "one-way-elevator"
    ONE_WAY_ANYTHING = "one-way-anything"

    @classmethod
    def default(cls) -> "LayoutElevators":
        return cls.VANILLA
