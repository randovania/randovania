import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck


class SkyTempleKeyHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> "SkyTempleKeyHintMode":
        return cls.PRECISE


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, DataclassPostInitTypeCheck):
    item_hints: bool = True
    sky_temple_keys: SkyTempleKeyHintMode = SkyTempleKeyHintMode.default()

    @classmethod
    def default(cls) -> "HintConfiguration":
        return cls()

    @property
    def as_json(self) -> dict:
        return {
            "item_hints": self.item_hints,
            "sky_temple_keys": self.sky_temple_keys.value,
        }

    @classmethod
    def from_json(cls, value: dict) -> "HintConfiguration":
        params = {}

        if "sky_temple_keys" in value:
            params["sky_temple_keys"] = SkyTempleKeyHintMode(value["sky_temple_keys"])

        if "item_hints" in value:
            params["item_hints"] = value["item_hints"]

        return cls(**params)
