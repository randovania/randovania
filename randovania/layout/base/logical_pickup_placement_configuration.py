from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class LogicalPickupPlacementConfiguration(BitPackEnum, Enum):
    long_name: str
    description: str

    MINIMAL = "minimal"
    MAJORS = "majors"
    ALL = "pickups"

    def dangerous_settings(self) -> list[str]:
        result = []
        if self is LogicalPickupPlacementConfiguration.ALL:
            result.append("Placing all pickups logically causes increased generation failure.")

        return result


enum_lib.add_long_name(
    LogicalPickupPlacementConfiguration,
    {
        LogicalPickupPlacementConfiguration.MINIMAL: "Minimal",
        LogicalPickupPlacementConfiguration.MAJORS: "Major pickups",
        LogicalPickupPlacementConfiguration.ALL: "All pickups",
    },
)

enum_lib.add_per_enum_field(
    LogicalPickupPlacementConfiguration,
    "description",
    {
        LogicalPickupPlacementConfiguration.MINIMAL: (
            "<b>Minimal</b>: Only the pickups required to beat the game are guaranteed to be obtainable."
        ),
        LogicalPickupPlacementConfiguration.MAJORS: (
            "<b>Major pickups</b>: Every major pickup in the preset is guaranteed to be obtainable."
        ),
        LogicalPickupPlacementConfiguration.ALL: (
            "<b>All pickups</b>: Every pickup in the preset, including ammo and expansions,"
            " is guaranteed to be obtainable.<br><br>"
            "<b>Warning</b>: Selecting 'All pickups' will make generation fail more frequently."
        ),
    },
)
