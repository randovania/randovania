from __future__ import annotations

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, order=True, slots=True)
class AreaIdentifier:
    region_name: str
    area_name: str

    def __post_init__(self):
        assert isinstance(self.region_name, str)
        assert isinstance(self.area_name, str)

    @property
    def as_json(self) -> dict:
        return {
            "region": self.region_name,
            "area": self.area_name,
        }

    @classmethod
    def from_json(cls, value: dict) -> Self:
        try:
            return cls(value["region"], value["area"])
        except Exception:
            raise

    @property
    def as_tuple(self) -> tuple[str, str]:
        return self.region_name, self.area_name

    @property
    def as_string(self) -> str:
        return f"{self.region_name}/{self.area_name}"

    @classmethod
    def from_string(cls, value: str) -> Self:
        return cls(*value.split("/", 1))

    def __repr__(self):
        return f"region {self.region_name}/area {self.area_name}"
