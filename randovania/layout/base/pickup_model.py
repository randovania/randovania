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

    @property
    def long_name(self):
        return MODEL_TYPE_PRETTY[self]


MODEL_TYPE_PRETTY = {
    PickupModelStyle.ALL_VISIBLE: "All visible",
    PickupModelStyle.HIDE_MODEL: "Hide model",
    PickupModelStyle.HIDE_SCAN: "Hide model and scan",
    PickupModelStyle.HIDE_ALL: "Hide all",
}


class PickupModelDataSource(BitPackEnum, Enum):
    ETM = "etm"
    RANDOM = "random"
    LOCATION = "location"

    @classmethod
    def default(cls) -> "PickupModelDataSource":
        return cls.ETM

    @property
    def long_name(self):
        return DATA_SOURCE_PRETTY[self]


DATA_SOURCE_PRETTY = {
    PickupModelDataSource.ETM: "ETM",
    PickupModelDataSource.RANDOM: "Random",
    PickupModelDataSource.LOCATION: "Vanilla",
}
