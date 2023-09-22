from __future__ import annotations

from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LocationCategory(BitPackEnum, Enum):
    long_name: str

    MAJOR = "major"
    MINOR = "minor"


enum_lib.add_long_name(
    LocationCategory,
    {
        LocationCategory.MAJOR: "Major",
        LocationCategory.MINOR: "Minor",
    },
)
