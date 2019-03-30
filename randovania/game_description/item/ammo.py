from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Ammo:
    name: str
    maximum: int
    items: Tuple[int, ...]
    temporaries: Tuple[int, ...] = tuple()
    models: Tuple[int, ...] = tuple()

    def __post_init__(self):
        if self.temporaries:
            if len(self.temporaries) != len(self.items):
                raise ValueError("If non-empty, temporaries must have the same size of items. Got {0} and {1}".format(
                    len(self.temporaries), len(self.items)
                ))

    @classmethod
    def from_json(cls, name: str, value: dict) -> "Ammo":
        return cls(
            name=name,
            maximum=value["maximum"],
            models=tuple(value["models"]),
            items=tuple(value["items"]),
            temporaries=tuple(value.get("temporaries", [])),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "maximum": self.maximum,
            "models": list(self.models),
            "items": list(self.items),
            "temporaries": list(self.temporaries),
        }
        return result
