from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LogicalPickupPlacementConfiguration(BitPackEnum, Enum):
    long_name: str

    MINIMAL = "minimal"
    MAJORS = "majors"
    ALL = "pickups"


enum_lib.add_long_name(
    LogicalPickupPlacementConfiguration,
    {
        LogicalPickupPlacementConfiguration.MINIMAL: "Minimal",
        LogicalPickupPlacementConfiguration.MAJORS: "Major pickups",
        LogicalPickupPlacementConfiguration.ALL: "All pickups",
    },
)
