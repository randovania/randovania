from __future__ import annotations

from enum import Enum
from typing import Self

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.lib import enum_lib


class PickupModelStyle(BitPackEnum, Enum):
    long_name: str

    ALL_VISIBLE = "all-visible"
    HIDE_MODEL = "hide-model"
    HIDE_SCAN = "hide-scan"
    HIDE_ALL = "hide-all"

    @classmethod
    def default(cls) -> Self:
        return cls.ALL_VISIBLE


enum_lib.add_long_name(
    PickupModelStyle,
    {
        PickupModelStyle.ALL_VISIBLE: "All visible",
        PickupModelStyle.HIDE_MODEL: "Hide model",
        PickupModelStyle.HIDE_SCAN: "Hide model and scan",
        PickupModelStyle.HIDE_ALL: "Hide all",
    },
)


class PickupModelDataSource(BitPackEnum, Enum):
    long_name: str

    ETM = "etm"
    RANDOM = "random"
    LOCATION = "location"

    @classmethod
    def default(cls) -> Self:
        return cls.ETM


enum_lib.add_long_name(
    PickupModelDataSource,
    {
        PickupModelDataSource.ETM: "ETM",
        PickupModelDataSource.RANDOM: "Random",
        PickupModelDataSource.LOCATION: "Vanilla",
    },
)
