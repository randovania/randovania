import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck


class ArtifactHintMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    HIDE_AREA = "hide-area"
    PRECISE = "precise"

    @classmethod
    def default(cls) -> "ArtifactHintMode":
        return cls.PRECISE


@dataclasses.dataclass(frozen=True)
class HintConfiguration(BitPackDataclass, DataclassPostInitTypeCheck):
    artifacts: ArtifactHintMode = ArtifactHintMode.default()

    @classmethod
    def default(cls) -> "HintConfiguration":
        return cls()

    @property
    def as_json(self) -> dict:
        return {
            "artifacts": self.artifacts.value,
        }

    @classmethod
    def from_json(cls, value: dict) -> "HintConfiguration":
        params = {}

        if "artifacts" in value:
            params["artifacts"] = ArtifactHintMode(value["artifacts"])

        return cls(**params)
