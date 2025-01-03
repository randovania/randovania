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
    # Precision hasn't been assigned yet
    UNDEFINED = "undefined"

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
    # Precision hasn't been assigned yet
    UNDEFINED = "undefined"

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


_PRECISION_PAIR_UNASSIGNED = PrecisionPair(
    location=HintLocationPrecision.UNDEFINED,
    item=HintItemPrecision.UNDEFINED,
    include_owner=False,
)


@dataclass(frozen=True)
class BaseHint(JsonDataclass):
    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> BaseHint:
        hint_type = HintType(json_dict["hint_type"])

        return hint_type.hint_class.from_json(json_dict, **extra)

    @property
    def as_json(self) -> dict:
        data = super().as_json
        data["hint_type"] = self.hint_type().value
        return data

    @classmethod
    def hint_type(cls) -> HintType:
        raise NotImplementedError


@dataclass(frozen=True)
class LocationHint(BaseHint):
    precision: PrecisionPair
    target: PickupIndex

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls(
            target=PickupIndex(json_dict["target"]),
            precision=PrecisionPair.from_json(json_dict["precision"]),
        )

    @classmethod
    def unassigned(cls, target: PickupIndex) -> typing.Self:
        """Creates a LocationHint without assigning its precision."""
        return cls(target=target, precision=_PRECISION_PAIR_UNASSIGNED)

    @classmethod
    def hint_type(cls) -> HintType:
        return HintType.LOCATION


def is_unassigned_location(hint: BaseHint) -> typing.TypeGuard[LocationHint]:
    return isinstance(hint, LocationHint) and (hint.precision is _PRECISION_PAIR_UNASSIGNED)


@dataclass(frozen=True)
class JokeHint(BaseHint):
    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls()

    @classmethod
    def hint_type(cls) -> HintType:
        return HintType.JOKE


@dataclass(frozen=True)
class RedTempleHint(BaseHint):
    dark_temple: HintDarkTemple

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        return cls(
            dark_temple=HintDarkTemple(json_dict["dark_temple"]),
        )

    @classmethod
    def hint_type(cls) -> HintType:
        return HintType.RED_TEMPLE_KEY_SET


Hint: typing.TypeAlias = LocationHint | JokeHint | RedTempleHint


class HintType(Enum):
    # Joke
    JOKE = "joke"

    # Hints for where a set of red temple keys are
    RED_TEMPLE_KEY_SET = "red-temple-key-set"

    # All other hints
    LOCATION = "location"

    hint_class: type[BaseHint]


HINT_TYPE_TO_CLASS = {cls.hint_type(): cls for cls in (LocationHint, JokeHint, RedTempleHint)}

enum_lib.add_per_enum_field(
    HintType,
    "hint_class",
    HINT_TYPE_TO_CLASS,
)
