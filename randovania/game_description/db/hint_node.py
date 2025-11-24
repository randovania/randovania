from __future__ import annotations

import dataclasses
from enum import Enum
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement


class HintNodeKind(Enum):
    long_name: str

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


@dataclasses.dataclass(frozen=True, slots=True)
class HintNode(ResourceNode):
    kind: HintNodeKind
    lock_requirement: Requirement

    def __repr__(self) -> str:
        return f"HintNode({self.name!r})"
