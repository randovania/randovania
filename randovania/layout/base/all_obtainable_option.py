from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class AllObtainableOption(BitPackEnum, Enum):
    long_name: str

    DISABLED = "disabled"
    MAJORS = "majors"
    ALL = "all"


enum_lib.add_long_name(
    AllObtainableOption,
    {
        AllObtainableOption.DISABLED: "Disabled",
        AllObtainableOption.MAJORS: "Majors only",
        AllObtainableOption.ALL: "All pickups",
    },
)
