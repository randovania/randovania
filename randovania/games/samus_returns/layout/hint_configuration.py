from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck


class ItemHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> ItemHintMode:
        return cls.PRECISE


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    artifacts: ItemHintMode
    baby_metroid: ItemHintMode
