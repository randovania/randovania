from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum


class PickupModelStyle(BitPackEnum, Enum):
    ALL_VISIBLE = "all-visible"
    HIDE_MODEL = "hide-model"
    HIDE_SCAN = "hide-scan"
    HIDE_ALL = "hide-all"

    @classmethod
    def default(cls) -> "PickupModelStyle":
        return cls.ALL_VISIBLE


class PickupModelDataSource(BitPackEnum, Enum):
    ETM = "etm"
    RANDOM = "random"
    LOCATION = "location"

    @classmethod
    def default(cls) -> "PickupModelDataSource":
        return cls.ETM
