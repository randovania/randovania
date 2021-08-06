from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutLogicalResourceAction(BitPackEnum, Enum):
    RANDOMLY = "randomly"
    LAST_RESORT = "last_resort"
    NEVER = "never"
