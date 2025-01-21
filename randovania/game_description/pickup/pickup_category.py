from __future__ import annotations

import dataclasses
from typing import NamedTuple

from randovania.bitpacking.json_dataclass import EXCLUDE_DEFAULT, JsonDataclass


class HintDetails(NamedTuple):
    determiner: str
    description: str


@dataclasses.dataclass(frozen=True, order=True)
class PickupCategory(JsonDataclass):
    name: str = dataclasses.field(metadata={"init_from_extra": True})
    long_name: str
    hint_details: HintDetails = dataclasses.field(metadata={"store_named_tuple_without_names": True})

    is_broad_category: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Used for Echoes Flying Ing Cache hints"""

    def __post_init__(self) -> None:
        assert self.name, "Name must not be empty"
        assert self.long_name, "Long name must not be empty"

    @property
    def general_details(self) -> tuple[str, str]:
        # FIXME
        return "an ", "item"


USELESS_PICKUP_CATEGORY = PickupCategory(
    name="useless",
    long_name="Useless",
    hint_details=("an ", "Energy Transfer Module"),
    is_broad_category=True,
)

GENERIC_KEY_CATEGORY = PickupCategory(
    name="key",
    long_name="Key",
    hint_details=("a ", "key"),
    is_broad_category=True,
)
