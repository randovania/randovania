from __future__ import annotations

from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LayoutLogicalResourceAction(BitPackEnum, Enum):
    long_name: str

    RANDOMLY = "randomly"
    LAST_RESORT = "last_resort"
    NEVER = "never"

    def is_default(self) -> bool:
        return self == LayoutLogicalResourceAction.RANDOMLY


enum_lib.add_long_name(
    LayoutLogicalResourceAction,
    {
        LayoutLogicalResourceAction.RANDOMLY: "Randomly",
        LayoutLogicalResourceAction.LAST_RESORT: "Last resort",
        LayoutLogicalResourceAction.NEVER: "Never",
    },
)
