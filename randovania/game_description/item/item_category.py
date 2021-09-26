from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True, order=True)
class ItemCategory:
    name: str
    long_name: str
    hint_details: Tuple[str, str]
    is_major_category: bool
    is_key: bool

    @classmethod
    def from_json(cls, name: str, value: dict) -> "ItemCategory":
        return cls(
            name=name,
            long_name=value["long_name"],
            hint_details=tuple(value["hint_details"]),
            is_major_category=value["is_major_category"],
            is_key=value["is_key"]
        )

    @property
    def general_details(self) -> Tuple[str, str]:
        if self.is_major_category:
            return "a ", "major upgrade"
        elif self.is_key:
            return "a ", "key"
        else:
            return "an ", "expansion"

NOTHING_CATEGORY = ItemCategory(
    name="nothing",
    long_name="",
    hint_details=["an ", "Energy Transfer Module"],
    is_major_category=False,
    is_key=False
)