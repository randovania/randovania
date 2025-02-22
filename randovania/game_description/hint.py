from __future__ import annotations

import dataclasses
import typing
from dataclasses import dataclass
from enum import Enum

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.bitpacking.type_enforcement import DataclassPostInitTypeCheck
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.hint_features import HintFeature
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.lib import enum_lib

if typing.TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.generator.hint_distributor import HintFeatureGaussianParams


class HintDarkTemple(Enum):
    AGON_WASTES = "agon-wastes"
    TORVUS_BOG = "torvus-bog"
    SANCTUARY_FORTRESS = "sanctuary-fortress"


class HintItemPrecision(Enum):
    # Precision hasn't been assigned yet
    UNDEFINED = "undefined"

    # Based on a feature of the item
    FEATURAL = "featural"

    # The exact item
    DETAILED = "detailed"


class HintLocationPrecision(Enum):
    # Precision hasn't been assigned yet
    UNDEFINED = "undefined"

    # Based on a feature of the location
    FEATURAL = "featural"

    # The exact location
    DETAILED = "detailed"

    # Includes only the region of the location
    REGION_ONLY = "region-only"

    # DEPRECATED: Relative hints
    RELATIVE_TO_AREA = "relative-to-area"
    RELATIVE_TO_INDEX = "relative-to-index"


@dataclass(frozen=True, order=True)
class SpecificHintPrecision(DataclassPostInitTypeCheck):
    """
    Can be used in a PrecisionPair to later be replaced with
    a HintFeature close to this exact precision.
    """

    mean: float = dataclasses.field(metadata={"min": 0.0, "max": 1.0})
    std_dev: float = dataclasses.field(default=0.0, metadata={"min": 0.0})

    @property
    def gauss_params(self) -> HintFeatureGaussianParams:
        return self.mean, self.std_dev


class HintRelativeAreaName(Enum):
    # The area's name
    NAME = "name"

    # Some unique feature of the area
    FEATURE = "feature"


@dataclass(frozen=True)
class RelativeData:
    distance_offset: int | None

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> RelativeDataItem | RelativeDataArea:
        if "area_location" in json_dict:
            return RelativeDataArea.from_json(json_dict, **extra)
        else:
            return RelativeDataItem.from_json(json_dict, **extra)


@dataclass(frozen=True)
class RelativeDataItem(JsonDataclass, RelativeData):
    other_index: PickupIndex
    precision: HintItemPrecision | HintFeature

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        pickup_database: PickupDatabase = extra["other_pickup_db"]

        item_json = json_dict.get("precision")
        item: HintItemPrecision | HintFeature
        if item_json is not None:
            item = HintItemPrecision(item_json)
        else:
            item = pickup_database.pickup_categories[json_dict["precision_feature"]]

        return cls(
            other_index=PickupIndex(json_dict["other_index"]),
            precision=item,
            distance_offset=json_dict["distance_offset"],
        )

    @property
    def as_json(self) -> dict:
        data = super().as_json
        if isinstance(self.precision, HintFeature):
            del data["precision"]
            data["precision_feature"] = self.precision.name
        return data


@dataclass(frozen=True)
class RelativeDataArea(JsonDataclass, RelativeData):
    area_location: AreaIdentifier
    precision: HintRelativeAreaName


@dataclass(frozen=True)
class PrecisionPair(JsonDataclass):
    location: HintLocationPrecision | HintFeature | SpecificHintPrecision
    item: HintItemPrecision | HintFeature | SpecificHintPrecision
    include_owner: bool | None = None
    relative: RelativeDataItem | RelativeDataArea | None = None

    @classmethod
    def from_json(cls, json_dict: dict, **extra: typing.Any) -> typing.Self:
        game: GameDescription = extra["game"]
        pickup_database: PickupDatabase = extra["pickup_db"]

        relative = json_dict.get("relative")

        location_json = json_dict.get("location")
        location: HintLocationPrecision | HintFeature
        if location_json is not None:
            location = HintLocationPrecision(location_json)
        else:
            location = game.hint_feature_database[json_dict["location_feature"]]

        item_json = json_dict.get("item")
        item: HintItemPrecision | HintFeature
        if item_json is not None:
            item = HintItemPrecision(item_json)
        else:
            item = pickup_database.pickup_categories[json_dict["item_feature"]]

        return cls(
            location=location,
            item=item,
            include_owner=json_dict["include_owner"],
            relative=RelativeData.from_json(relative, **extra) if relative is not None else None,
        )

    @property
    def as_json(self) -> dict:
        if isinstance(self.location, SpecificHintPrecision) or isinstance(self.item, SpecificHintPrecision):
            raise TypeError(f"PrecisionPair {self} with SpecificHintPrecision is not JSON encodable!")

        data = super().as_json
        if isinstance(self.location, HintFeature):
            del data["location"]
            data["location_feature"] = self.location.name
        if isinstance(self.item, HintFeature):
            del data["item"]
            data["item_feature"] = self.item.name
        return data

    @classmethod
    def featural(cls) -> typing.Self:
        """A default PrecisionPair with both precisions set to FEATURAL and include_owner set to None"""
        return cls(
            location=HintLocationPrecision.FEATURAL,
            item=HintItemPrecision.FEATURAL,
        )


PRECISION_PAIR_UNASSIGNED = PrecisionPair(
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
            precision=PrecisionPair.from_json(json_dict["precision"], **extra),
        )

    @classmethod
    def unassigned(cls, target: PickupIndex) -> typing.Self:
        """Creates a LocationHint without assigning its precision."""
        return cls(target=target, precision=PRECISION_PAIR_UNASSIGNED)

    @classmethod
    def hint_type(cls) -> HintType:
        return HintType.LOCATION


def is_unassigned_location(hint: BaseHint) -> typing.TypeGuard[LocationHint]:
    return isinstance(hint, LocationHint) and (
        (hint.precision is PRECISION_PAIR_UNASSIGNED)
        or (hint.precision.location is HintLocationPrecision.FEATURAL)
        or (hint.precision.item is HintItemPrecision.FEATURAL)
        or isinstance(hint.precision.location, SpecificHintPrecision)
        or isinstance(hint.precision.item, SpecificHintPrecision)
    )


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
