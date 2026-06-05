from __future__ import annotations

import dataclasses
from enum import Enum
from typing import TYPE_CHECKING, final, override

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement


@dataclasses.dataclass(frozen=True, slots=True)
class HintNode(ResourceNode):
    requirement_to_collect: Requirement

    def __repr__(self) -> str:
        return f"HintNode({self.name!r})"

    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        raise NotImplementedError

    @final
    @property
    def kind(self) -> HintNodeKind:
        return self.hint_kind()


@dataclasses.dataclass(frozen=True, slots=True)
class GenericHintNode(HintNode):
    @override
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.GENERIC


@dataclasses.dataclass(frozen=True, slots=True)
class SpecificLocationHintNode(HintNode):
    target_index: PickupIndex
    """Which PickupIndex this hint points to."""

    @override
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.SPECIFIC_LOCATION


@dataclasses.dataclass(frozen=True, slots=True)
class SpecificPickupHintNode(HintNode):
    specific_pickup_hint_id: str
    """Which entry in `GameHints.specific_pickup_hints` this hint is for."""

    @override
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.SPECIFIC_PICKUP


class HintNodeKind(Enum):
    long_name: str
    hint_node_class: type[HintNode]

    GENERIC = "generic"
    SPECIFIC_LOCATION = "specific-location"
    SPECIFIC_PICKUP = "specific-pickup"


enum_lib.add_long_name(
    HintNodeKind,
    {
        HintNodeKind.GENERIC: "Generic",
        HintNodeKind.SPECIFIC_LOCATION: "Specific Location",
        HintNodeKind.SPECIFIC_PICKUP: "Specific Pickup",
    },
)

enum_lib.add_per_enum_field(
    HintNodeKind,
    "hint_node_class",
    {cls.hint_kind(): cls for cls in HintNode.__subclasses__()},
)
