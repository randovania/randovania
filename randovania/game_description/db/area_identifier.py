from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, order=True, slots=True)
class AreaIdentifier:
    region: str
    area: str

    def __post_init__(self) -> None:
        assert isinstance(self.region, str)
        assert isinstance(self.area, str)

    @property
    def as_json(self) -> dict:
        return {
            "region": self.region,
            "area": self.area,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        try:
            return cls(value["region"], value["area"])
        except Exception:
            raise

    @property
    def as_tuple(self) -> tuple[str, str]:
        return self.region, self.area

    @property
    def as_string(self) -> str:
        return f"{self.region}/{self.area}"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(*value.split("/", 1))

    def __repr__(self) -> str:
        return f"region {self.region}/area {self.area}"
