from __future__ import annotations

import dataclasses
from typing import NamedTuple

from randovania.bitpacking.json_dataclass import EXCLUDE_DEFAULT, JsonDataclass


class HintDetails(NamedTuple):
    determiner: str
    """
    The standard determiner ('a ', 'an ', 'the ') for these details.
    Should always have a trailing space if it isn't empty.
    """

    description: str
    """The identifying feature of these hint details."""


@dataclasses.dataclass(frozen=True, order=True)
class HintFeature(JsonDataclass):
    """
    A feature for categorizing PickupEntry, PickupNode, Area, and anything else that benefits from "tags" such as this.
    Primarily intended for use with the Featural Hint system
    """

    name: str = dataclasses.field(metadata={"init_from_extra": True})
    long_name: str
    hint_details: HintDetails = dataclasses.field(metadata={"store_named_tuple_without_names": True})

    def __post_init__(self) -> None:
        assert self.name, "Name must not be empty"
        assert self.long_name, "Long name must not be empty"


@dataclasses.dataclass(frozen=True, order=True)
class PickupHintFeature(HintFeature):
    """Specialized HintFeature for PickupEntry, which has additional needs over basic HintFeatures"""

    # TODO: refactor out eventually (migration necessary)
    is_broad_category: bool = dataclasses.field(default=False, metadata=EXCLUDE_DEFAULT)
    """Used for Echoes Flying Ing Cache hints"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}')"
