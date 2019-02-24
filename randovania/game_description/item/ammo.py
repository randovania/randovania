from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class Ammo:
    name: str
    models: Tuple[int, ...]
    item: int
    maximum: int

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            models=tuple(value["models"]),
            item=value["item"],
            maximum=value["maximum"],
        )

    @property
    def as_json(self) -> dict:
        return {
            "models": list(self.models),
            "item": self.item,
            "maximum": self.maximum,
        }
