from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True, order=True)
class ItemCategory:
    name: str
    long_name: str
    hint_details: Tuple[str, str]
    is_major: bool

    @classmethod
    def from_json(cls, name: str, value: dict) -> "ItemCategory":
        return cls(
            name=name,
            long_name=value["long_name"],
            hint_details=tuple(value["hint_details"]),
            is_major=value["is_major"]
        )

    @property
    def general_details(self) -> Tuple[str, str]:
        if self.is_major:
            return "a ", "major upgrade"
        return self.hint_details
    
    @property
    def is_expansion(self) -> bool:
        return self.name == "expansion"

    @property
    def is_key(self) -> bool:
        return self.name ==  "key"


USELESS_ITEM_CATEGORY = ItemCategory(
    name="useless",
    long_name="",
    hint_details=["an ", "Energy Transfer Module"],
    is_major=False
)

GENERIC_KEY_CATEGORY = ItemCategory(
    name="key",
    long_name="",
    hint_details=["a ", "key"],
    is_major=False
)
