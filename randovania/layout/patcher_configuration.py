import copy
import dataclasses
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


_DAMAGE_METADATA = {"min": 0.0, "max": 60.0, "precision": 2.0}


def _with_default(default: float) -> dict:
    metadata = copy.copy(_DAMAGE_METADATA)
    metadata["if_different"] = default
    return metadata


@dataclasses.dataclass(frozen=True)
class PatcherConfiguration(BitPackDataClass):
    menu_mod: bool = True
    warp_to_start: bool = True
    varia_suit_damage: float = dataclasses.field(default=6.0, metadata=_with_default(6.0))
    dark_suit_damage: float = dataclasses.field(default=1.2, metadata=_with_default(1.2))
    pickup_model_style: PickupModelStyle = PickupModelStyle.default()
    pickup_model_data_source: PickupModelDataSource = PickupModelDataSource.default()

    @property
    def as_json(self) -> dict:
        return {
            "menu_mod": self.menu_mod,
            "warp_to_start": self.warp_to_start,
            "varia_suit_damage": self.varia_suit_damage,
            "dark_suit_damage": self.dark_suit_damage,
            "pickup_model_style": self.pickup_model_style.value,
            "pickup_model_data_source": self.pickup_model_data_source.value,
        }

    @classmethod
    def from_json_dict(cls, json_dict: dict) -> "PatcherConfiguration":
        kwargs = {}

        for field in dataclasses.fields(cls):
            field: dataclasses.Field = field
            if field.name in json_dict:
                kwargs[field.name] = field.type(json_dict[field.name])

        return PatcherConfiguration(**kwargs)

    @classmethod
    def default(cls) -> "PatcherConfiguration":
        return PatcherConfiguration()
