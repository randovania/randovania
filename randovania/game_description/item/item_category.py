from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True, order=True)
class ItemCategory:
    name: str
    long_name: str
    hint_details: Tuple[str, str]
    is_major: bool
    is_key: bool = False

    @classmethod
    def from_json(cls, name: str, value: dict) -> "ItemCategory":
        return cls(
            name=name,
            long_name=value["long_name"],
            hint_details=tuple(value["hint_details"]),
            is_major=value["is_major"],
            is_key=value["is_key"] if "is_key" in value else False
        )

    @property
    def as_json(self) -> dict:
        result = {
            "long_name": self.long_name,
            "hint_details": list(self.hint_details),
            "is_major": self.is_major,
        }
        if self.is_key:
            result["is_key"] = self.is_key
        return result

    @property
    def general_details(self) -> Tuple[str, str]:
        if self.is_major:
            return "a ", "major upgrade"
        elif self.is_key:
            return "a ", "key"
        else:
            return "an ", "expansion"

    @property
    def is_expansion(self) -> bool:
        return self.name == "expansion"


USELESS_ITEM_CATEGORY = ItemCategory(
    name="useless",
    long_name="",
    hint_details=("an ", "Energy Transfer Module"),
    is_major=False
)

GENERIC_KEY_CATEGORY = ItemCategory(
    name="key",
    long_name="",
    hint_details=("a ", "key"),
    is_major=False
)
