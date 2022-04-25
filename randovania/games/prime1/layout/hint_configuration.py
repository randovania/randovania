import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck


class ArtifactHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> "ArtifactHintMode":
        return cls.PRECISE

class PhazonSuitHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> "PhazonSuitHintMode":
        return cls.PRECISE

@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, JsonDataclass, DataclassPostInitTypeCheck):
    artifacts: ArtifactHintMode
    phazon_suit: PhazonSuitHintMode
