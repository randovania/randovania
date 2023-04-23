from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LocationCategory(BitPackEnum, Enum):
    MAJOR = "major"
    MINOR = "minor"

    @property
    def long_name(self) -> str:
        if self == LocationCategory.MAJOR:
            return "Major"
        elif self == LocationCategory.MINOR:
            return "Minor"
        else:
            raise ValueError(f"Unknown: {self}")
