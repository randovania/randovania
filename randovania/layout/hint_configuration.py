import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataClass, BitPackEnum


class SkyTempleKeyHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> "SkyTempleKeyHintMode":
        return cls.PRECISE


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataClass):
    sky_temple_keys: SkyTempleKeyHintMode = SkyTempleKeyHintMode.default()

    @classmethod
    def default(cls) -> "HintConfiguration":
        return cls()

    @property
    def as_json(self) -> dict:
        return {
            "sky_temple_keys": self.sky_temple_keys.value,
        }

    @classmethod
    def from_json(cls, value: dict) -> "HintConfiguration":
        params = {}

        if "sky_temple_keys" in value:
            params["sky_temple_keys"] = SkyTempleKeyHintMode(value["sky_temple_keys"])

        return cls(**params)

