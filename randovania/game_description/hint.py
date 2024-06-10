from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.resources.pickup_index import PickupIndex


class HintType(Enum):
    # Joke
    JOKE = "joke"

    # Hints for where a set of red temple keys are
    RED_TEMPLE_KEY_SET = "red-temple-key-set"

    # All other hints
    LOCATION = "location"


class HintDarkTemple(Enum):
    AGON_WASTES = "agon-wastes"
    TORVUS_BOG = "torvus-bog"
    SANCTUARY_FORTRESS = "sanctuary-fortress"


class HintItemPrecision(Enum):
    # The exact item
    DETAILED = "detailed"

    # movement, morph ball, etc
    PRECISE_CATEGORY = "precise-category"

    # major item, key, expansion
    GENERAL_CATEGORY = "general-category"

    # x-related, life-support, or just the precise category
    BROAD_CATEGORY = "broad-category"

    # Say nothing at all about the item
    NOTHING = "nothing"


class HintLocationPrecision(Enum):
    # The exact location
    DETAILED = "detailed"

    # Includes only the region of the location
    REGION_ONLY = "region-only"

    # Keybearer corpses
    KEYBEARER = "keybearer"

    # Amorbis, Chykka, and Quadraxis
    GUARDIAN = "guardian"

    # Vanilla Light Suit location
    LIGHT_SUIT_LOCATION = "light-suit-location"

    RELATIVE_TO_AREA = "relative-to-area"
    RELATIVE_TO_INDEX = "relative-to-index"

    MALCO = "malco"
    JENKA = "jenka"
    LITTLE = "mrs-little"
    NUMAHACHI = "numahachi"


class HintRelativeAreaName(Enum):
    # The area's name
    NAME = "name"

    # Some unique feature of the area
    FEATURE = "feature"


@dataclass(frozen=True)
class RelativeData:
    distance_offset: int | None

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> RelativeData:
        if "area_location" in json_dict:
            return RelativeDataArea.from_json(json_dict)
        else:
            return RelativeDataItem.from_json(json_dict)


@dataclass(frozen=True)
class RelativeDataItem(JsonDataclass, RelativeData):  # type: ignore[misc]
    other_index: PickupIndex
    precision: HintItemPrecision


@dataclass(frozen=True)
class RelativeDataArea(JsonDataclass, RelativeData):  # type: ignore[misc]
    area_location: AreaIdentifier
    precision: HintRelativeAreaName


@dataclass(frozen=True)
class PrecisionPair(JsonDataclass):
    location: HintLocationPrecision
    item: HintItemPrecision
    include_owner: bool
    relative: RelativeData | None = None

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        # re-implemented for an version without expensive reflection
        relative = json_dict.get("relative")

        return cls(
            location=HintLocationPrecision(json_dict["location"]),
            item=HintItemPrecision(json_dict["item"]),
            include_owner=json_dict["include_owner"],
            relative=RelativeData.from_json(relative) if relative is not None else None,
        )


@dataclass(frozen=True)
class Hint(JsonDataclass):
    hint_type: HintType
    precision: PrecisionPair | None
    target: PickupIndex | None = None
    dark_temple: HintDarkTemple | None = None

    def __post_init__(self) -> None:
        if self.hint_type is HintType.JOKE:
            if self.target is not None or self.dark_temple is not None:
                raise ValueError("Joke Hint, but had a target or dark_temple.")
        elif self.hint_type is HintType.LOCATION:
            if self.target is None:
                raise ValueError("Location Hint, but no target set.")
        elif self.hint_type is HintType.RED_TEMPLE_KEY_SET:
            if self.dark_temple is None:
                raise ValueError("Dark Temple Hint, but no dark_temple set.")

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        # re-implemented for an version without expensive reflection
        precision = json_dict.get("precision")
        target = json_dict.get("target")
        dark_temple = json_dict.get("dark_temple")

        return cls(
            hint_type=HintType(json_dict["hint_type"]),
            precision=PrecisionPair.from_json(precision) if precision is not None else None,
            target=PickupIndex(target) if target is not None else None,
            dark_temple=HintDarkTemple(dark_temple) if dark_temple is not None else None,
        )
