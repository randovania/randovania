from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Ammo:
    name: str
    models: List[int]
    item: int
    maximum: int

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            models=value["models"],
            item=value["item"],
            maximum=value["maximum"],
        )

    @property
    def as_json(self) -> dict:
        return {
            "models": self.models,
            "item": self.item,
            "maximum": self.maximum,
        }
