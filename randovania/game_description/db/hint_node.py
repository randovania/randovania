from __future__ import annotations

import dataclasses
from enum import Enum
from typing import TYPE_CHECKING, Any

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain


@dataclasses.dataclass(frozen=True, slots=True)
class HintNode(ResourceNode):
    lock_requirement: Requirement
    requirement_display_name: str | None
    _target: Any

    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        raise NotImplementedError

    @property
    def kind(self) -> HintNodeKind:
        return self.hint_kind()

    def __repr__(self) -> str:
        return f"HintNode({self.name!r})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return self.lock_requirement

    def requirement_to_collect(self) -> Requirement:
        return self.lock_requirement

    @property
    def requirement_name(self) -> str:
        return self.requirement_display_name or str(self.lock_requirement)

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.resource(context))

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(context), 1

    def data_editor_message(self, region_list: RegionList, db: ResourceDatabase) -> str:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True, slots=True)
class GenericHintNode(HintNode):
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.GENERIC

    def data_editor_message(self, region_list: RegionList, db: ResourceDatabase) -> str:
        message = "Generic Hint"
        if (requirement := self.requirement_name) != "Trivial":
            message += f"\n<br />Requirement: {requirement}"
        return message


@dataclasses.dataclass(frozen=True, slots=True)
class SpecificLocationHintNode(HintNode):
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.SPECIFIC_LOCATION

    @property
    def target_index(self) -> PickupIndex:
        """Which PickupIndex this hint points to."""
        return PickupIndex(self._target)

    def data_editor_message(self, region_list: RegionList, db: ResourceDatabase) -> str:
        message = "Specific Location Hint"
        target = region_list.node_from_pickup_index(self.target_index)
        fmt_message = '\n<br />Target: <a href="node://{}">{}</a>'
        message += fmt_message.format(
            target.identifier.as_string,
            region_list.node_name(target, True, True),
        )
        if (requirement := self.requirement_name) != "Trivial":
            message += f"\n<br />Requirement: {requirement}"
        return message


@dataclasses.dataclass(frozen=True, slots=True)
class SpecificPickupHintNode(HintNode):
    @classmethod
    def hint_kind(cls) -> HintNodeKind:
        return HintNodeKind.SPECIFIC_PICKUP

    @property
    def specific_pickup_hint_id(self) -> str:
        """Which entry in `GameHints.specific_pickup_hints` this hint is for."""
        return self._target

    def data_editor_message(self, region_list: RegionList, db: ResourceDatabase) -> str:
        message = "Specific Pickup Hint"
        details = db.game_enum.hints.specific_pickup_hints[self.specific_pickup_hint_id]
        message += f"\n<br />Target: {details.long_name}"
        if (requirement := self.requirement_name) != "Trivial":
            message += f"\n<br />Requirement: {requirement}"
        return message


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

HINT_KIND_TO_CLASS = {
    cls.hint_kind(): cls for cls in (GenericHintNode, SpecificLocationHintNode, SpecificPickupHintNode)
}

enum_lib.add_per_enum_field(
    HintNodeKind,
    "hint_node_class",
    HINT_KIND_TO_CLASS,
)
