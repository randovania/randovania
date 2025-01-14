from __future__ import annotations

import dataclasses

from randovania.lib import frozen_lib


@dataclasses.dataclass(frozen=True, order=True)
class PickupCategory:
    name: str
    long_name: str
    hint_details: tuple[str, str]

    def __post_init__(self) -> None:
        assert self.name, "Name must not be empty"
        assert self.long_name, "Long name must not be empty"
        assert len(self.hint_details) == 2, "Hint details must be 2 elements"

    @classmethod
    def from_json(cls, name: str, value: dict) -> PickupCategory:
        return cls(
            name=name,
            long_name=value["long_name"],
            hint_details=frozen_lib.wrap(value["hint_details"]),
        )

    @property
    def as_json(self) -> dict:
        result = {
            "long_name": self.long_name,
            "hint_details": frozen_lib.unwrap(self.hint_details),
        }
        return result

    @property
    def general_details(self) -> tuple[str, str]:
        # FIXME
        return "an ", "item"


USELESS_PICKUP_CATEGORY = PickupCategory(
    name="useless",
    long_name="Useless",
    hint_details=("an ", "Energy Transfer Module"),
)

GENERIC_KEY_CATEGORY = PickupCategory(name="key", long_name="Key", hint_details=("a ", "key"))
