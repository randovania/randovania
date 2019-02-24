from dataclasses import dataclass
from typing import List, Tuple, Optional


@dataclass(frozen=True)
class Ammo:
    name: str
    models: Tuple[int, ...]
    items: Tuple[int, ...]
    maximum: int

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            models=tuple(value["models"]),
            items=tuple(value["items"]),
            maximum=value["maximum"],
        )

    @property
    def as_json(self) -> dict:
        result = {
            "models": list(self.models),
            "items": list(self.items),
            "maximum": self.maximum,
        }
        return result
