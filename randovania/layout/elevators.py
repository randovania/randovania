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

    @property
    def long_name(self) -> str:
        if self == LayoutElevators.VANILLA:
            return "Original connections"
        elif self == LayoutElevators.TWO_WAY_RANDOMIZED:
            return "Two-way, between areas"
        elif self == LayoutElevators.TWO_WAY_UNCHECKED:
            return "Two-way, unchecked"
        elif self == LayoutElevators.ONE_WAY_ELEVATOR:
            return "One-way, elevator room"
        elif self == LayoutElevators.ONE_WAY_ANYTHING:
            return "One-way, anywhere"
        else:
            raise ValueError(f"Unknown value: {self}")
