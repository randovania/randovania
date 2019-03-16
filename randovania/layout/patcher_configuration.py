from dataclasses import dataclass
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataClass, BitPackEnum


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


@dataclass(frozen=True)
class PatcherConfiguration(BitPackDataClass):
    menu_mod: bool = True
    warp_to_start: bool = True
    pickup_model_style: PickupModelStyle = PickupModelStyle.default()
    pickup_model_data_source: PickupModelDataSource = PickupModelDataSource.default()

    @property
    def as_json(self) -> dict:
        return {
            "menu_mod": self.menu_mod,
            "warp_to_start": self.warp_to_start,
            "pickup_model_style": self.pickup_model_style.value,
            "pickup_model_data_source": self.pickup_model_data_source.value,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PatcherConfiguration":
        return PatcherConfiguration(
            menu_mod=json_dict["menu_mod"],
            warp_to_start=json_dict["warp_to_start"],
            pickup_model_style=PickupModelStyle(json_dict["pickup_model_style"]),
            pickup_model_data_source=PickupModelDataSource(json_dict["pickup_model_data_source"]),
        )

    @classmethod
    def default(cls) -> "PatcherConfiguration":
        return PatcherConfiguration()
