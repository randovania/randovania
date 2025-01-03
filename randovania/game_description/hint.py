from __future__ import annotations

import typing
from dataclasses import dataclass
from enum import Enum

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.lib import enum_lib


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
    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> Hint:
        hint_type = HintType(json_dict["hint_type"])

        return hint_type.hint_class.from_json(json_dict, **extra)


@dataclass(frozen=True)
class LocationHint(Hint):
    precision: PrecisionPair | None
    target: PickupIndex

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls(
            target=PickupIndex(json_dict["target"]),
            precision=PrecisionPair.from_json(json_dict["precision"]),
        )


@dataclass(frozen=True)
class JokeHint(Hint):
    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls()


@dataclass(frozen=True)
class RedTempleHint(Hint):
    dark_temple: HintDarkTemple

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls(
            dark_temple=HintDarkTemple(json_dict["dark_temple"]),
        )


class HintType(Enum):
    # Joke
    JOKE = "joke"

    # Hints for where a set of red temple keys are
    RED_TEMPLE_KEY_SET = "red-temple-key-set"

    # All other hints
    LOCATION = "location"

    hint_class: type[Hint]


enum_lib.add_per_enum_field(
    HintType,
    "hint_class",
    {
        HintType.LOCATION: LocationHint,
        HintType.JOKE: JokeHint,
        HintType.RED_TEMPLE_KEY_SET: RedTempleHint,
    },
)
