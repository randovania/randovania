from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class LayoutLogicalResourceAction(BitPackEnum, Enum):
    RANDOMLY = "randomly"
    LAST_RESORT = "last_resort"
    NEVER = "never"

    @property
    def long_name(self) -> str:
        return PRETTY_NAME[self]

    def is_default(self) -> bool:
        return self == LayoutLogicalResourceAction.RANDOMLY


PRETTY_NAME = {
    LayoutLogicalResourceAction.RANDOMLY: "Randomly",
    LayoutLogicalResourceAction.LAST_RESORT: "Last resort",
    LayoutLogicalResourceAction.NEVER: "Never",
}
