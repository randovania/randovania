from dataclasses import dataclass

from randovania.lib import frozen_lib


@dataclass(frozen=True, order=True)
class ItemCategory:
    name: str
    long_name: str
    hint_details: tuple[str, str]
    is_major: bool
    is_key: bool = False

    def __post_init__(self):
        assert self.name, "Name must not be empty"
        assert self.long_name, "Long name must not be empty"
        assert len(self.hint_details) == 2, "Hint details must be 2 elements"

    @classmethod
    def from_json(cls, name: str, value: dict) -> "ItemCategory":
        return cls(
            name=name,
            long_name=value["long_name"],
            hint_details=frozen_lib.wrap(value["hint_details"]),
            is_major=value["is_major"],
            is_key=value["is_key"] if "is_key" in value else False
        )

    @property
    def as_json(self) -> dict:
        result = {
            "long_name": self.long_name,
            "hint_details": frozen_lib.unwrap(self.hint_details),
            "is_major": self.is_major,
        }
        if self.is_key:
            result["is_key"] = self.is_key
        return result

    @property
    def general_details(self) -> tuple[str, str]:
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
    long_name="Useless",
    hint_details=("an ", "Energy Transfer Module"),
    is_major=False
)

GENERIC_KEY_CATEGORY = ItemCategory(
    name="key",
    long_name="Key",
    hint_details=("a ", "key"),
    is_major=False
)
