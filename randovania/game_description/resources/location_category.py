from enum import Enum


class LocationCategory(Enum):
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
